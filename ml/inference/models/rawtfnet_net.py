"""
RawTFNet PyTorch Architecture definition.
Paper: "RawTFNet: A Lightweight CNN Architecture for Speech Anti-spoofing" (Xiao, Dang & Das, 2025)
Official repo: https://github.com/swagshaw/RawTFNet-Pytorch
Checkpoint: Best_RawTFNet_32.pth (177,540 parameters)
"""

import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class SincConv(nn.Module):
    """
    Sinc-based convolution layer for raw audio waveforms.
    Computes bandpass filter sinc functions.
    """
    @staticmethod
    def to_mel(hz):
        return 2595 * np.log10(1 + hz / 700)

    @staticmethod
    def to_hz(mel):
        return 700 * (10 ** (mel / 2595) - 1)

    def __init__(
        self,
        out_channels: int,
        kernel_size: int,
        sample_rate: int = 16000,
        in_channels: int = 1,
        stride: int = 1,
        padding: int = 0,
        dilation: int = 1,
        bias: bool = False,
        groups: int = 1,
        min_low_hz: int = 0,
        min_band_hz: int = 50,
    ):
        super().__init__()
        if in_channels != 1:
            raise ValueError(f"SincConv only supports in_channels=1, got {in_channels}")
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        if kernel_size % 2 == 0:
            self.kernel_size = kernel_size + 1
        self.stride = stride
        self.padding = padding
        self.dilation = dilation
        self.sample_rate = sample_rate
        self.min_low_hz = min_low_hz
        self.min_band_hz = min_band_hz

        # Initialize filterbanks mel-spaced
        low_hz = 30
        high_hz = self.sample_rate / 2 - (self.min_low_hz + self.min_band_hz)
        mel = np.linspace(self.to_mel(low_hz), self.to_mel(high_hz), self.out_channels + 1)
        hz = self.to_hz(mel)

        # Learnable filter parameters
        self.low_hz_ = nn.Parameter(torch.Tensor(hz[:-1]).view(-1, 1))
        self.band_hz_ = nn.Parameter(torch.Tensor(np.diff(hz)).view(-1, 1))

        # Hamming window
        n_lin = torch.linspace(0, (self.kernel_size / 2) - 1, steps=int((self.kernel_size / 2)))
        self.window_ = 0.54 - 0.46 * torch.cos(2 * math.pi * n_lin / self.kernel_size)

        n = (self.kernel_size - 1) / 2.0
        self.n_ = 2 * math.pi * torch.arange(-n, 0).view(1, -1) / self.sample_rate

    def forward(self, waveforms):
        self.n_ = self.n_.to(waveforms.device)
        self.window_ = self.window_.to(waveforms.device)

        low = self.min_low_hz + torch.abs(self.low_hz_)
        high = torch.clamp(low + self.min_band_hz + torch.abs(self.band_hz_), self.min_low_hz, self.sample_rate / 2)
        band = (high - low)[:, 0]

        f_times_t_low = torch.matmul(low, self.n_)
        f_times_t_high = torch.matmul(high, self.n_)

        band_pass_left = ((torch.sin(f_times_t_high) - torch.sin(f_times_t_low)) / (self.n_ / 2)) * self.window_
        band_pass_center = 2 * band.view(-1, 1)
        band_pass_right = torch.flip(band_pass_left, dims=[1])

        band_pass = torch.cat([band_pass_left, band_pass_center, band_pass_right], dim=1)
        band_pass = band_pass / (2 * band[:, None])

        filters = band_pass.view(self.out_channels, 1, self.kernel_size)
        return F.conv1d(
            waveforms,
            filters,
            stride=self.stride,
            padding=self.padding,
            dilation=self.dilation,
            bias=None,
            groups=1,
        )


class SeparableConv2d(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size, stride=1, padding=0, dilation=1, bias=False, pointwise=False):
        super().__init__()
        self.conv2d = nn.Conv2d(
            in_channels=in_channels,
            out_channels=in_channels,
            kernel_size=kernel_size,
            stride=stride,
            groups=in_channels,
            padding=padding,
            dilation=dilation,
            bias=bias,
        )
        if pointwise:
            self.pointwise = nn.Conv2d(in_channels=in_channels, out_channels=out_channels, kernel_size=1, stride=1, padding=0, bias=bias)
        else:
            self.pointwise = nn.Identity()

    def forward(self, x):
        return self.pointwise(self.conv2d(x))


class SELayer(nn.Module):
    def __init__(self, channel, reduction=16):
        super().__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(channel, channel // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(channel // reduction, channel, bias=False),
            nn.Sigmoid(),
        )

    def forward(self, x):
        b, c, _, _ = x.size()
        y = self.avg_pool(x).view(b, c)
        y = self.fc(y).view(b, c, 1, 1)
        return x * y.expand_as(x)


class Res2NetBlock(nn.Module):
    def __init__(self, in_channels, out_channels, scale=4, stride=1, dilation=1):
        super().__init__()
        self.scale = scale
        self.width = out_channels // scale
        self.nums = scale - 1
        self.convs = nn.ModuleList([
            nn.Conv2d(self.width, self.width, kernel_size=3, stride=stride, padding=dilation, dilation=dilation, bias=False)
            for _ in range(self.nums)
        ])
        self.bns = nn.ModuleList([nn.BatchNorm2d(self.width) for _ in range(self.nums)])
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        spx = torch.split(x, self.width, 1)
        out = []
        for i in range(self.nums):
            if i == 0:
                sp = spx[i]
            else:
                sp = sp + spx[i]
            sp = self.convs[i](sp)
            sp = self.relu(self.bns[i](sp))
            out.append(sp)
        out.append(spx[self.nums])
        return torch.cat(out, 1)


class DWS_Res2Net_SE_Block(nn.Module):
    def __init__(self, in_channels, out_channels, scale=4, stride=1, reduction=16):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.res2net = Res2NetBlock(out_channels, out_channels, scale=scale, stride=stride)
        self.conv3 = nn.Conv2d(out_channels, out_channels, kernel_size=1, bias=False)
        self.bn3 = nn.BatchNorm2d(out_channels)
        self.se = SELayer(out_channels, reduction=reduction)
        self.relu = nn.ReLU(inplace=True)

        if in_channels != out_channels or stride != 1:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(out_channels),
            )
        else:
            self.shortcut = nn.Identity()

    def forward(self, x):
        residual = self.shortcut(x)
        out = self.relu(self.bn1(self.conv1(x)))
        out = self.res2net(out)
        out = self.bn3(self.conv3(out))
        out = self.se(out)
        out = self.relu(out + residual)
        return out


class DWS_Frontend_SE(nn.Module):
    def __init__(self, sinc_kernel_size: int = 128, sample_rate: int = 16000):
        super().__init__()
        self.sinc_conv = SincConv(out_channels=70, kernel_size=sinc_kernel_size, sample_rate=sample_rate)
        self.bn = nn.BatchNorm2d(1)
        self.conv_blocks = nn.Sequential(
            DWS_Res2Net_SE_Block(1, 32, scale=4),
            nn.MaxPool2d((2, 2)),
            DWS_Res2Net_SE_Block(32, 64, scale=4),
            nn.MaxPool2d((2, 2)),
            DWS_Res2Net_SE_Block(64, 32, scale=4),
            nn.MaxPool2d((2, 2)),
        )

    def forward(self, x):
        # x shape: (B, T)
        if x.ndim == 2:
            x = x.unsqueeze(1)  # (B, 1, T)
        x = self.sinc_conv(x)   # (B, 70, T')
        x = x.unsqueeze(1)      # (B, 1, 70, T')
        x = self.bn(x)
        x = self.conv_blocks(x) # (B, 32, F', T'')
        return x


class ShuffleLayer(nn.Module):
    def __init__(self, group=8):
        super().__init__()
        self.group = group

    def forward(self, x):
        b, c, f, t = x.size()
        if c % self.group != 0:
            return x
        group_channels = c // self.group
        x = x.reshape(b, group_channels, self.group, f, t)
        x = x.permute(0, 2, 1, 3, 4)
        x = x.reshape(b, c, f, t)
        return x


class AdaResNorm(nn.Module):
    def __init__(self, c, grad=False, eps=1e-5):
        super().__init__()
        self.grad = grad
        self.register_buffer("eps", torch.tensor([eps]).view(1, 1, 1, 1))
        self.register_buffer("rho", torch.tensor([0.5]).view(1, 1, 1, 1))

    def forward(self, x):
        identity = x
        ifn_mean = x.mean((1, 3), keepdim=True)
        ifn_var = x.var((1, 3), keepdim=True)
        ifn = (x - ifn_mean) / torch.sqrt(ifn_var + self.eps)
        return self.rho * identity + (1.0 - self.rho) * ifn


class TfSepBlock(nn.Module):
    def __init__(self, channels, dropout_rate=0.2):
        super().__init__()
        self.norm1 = AdaResNorm(channels)
        self.time_conv = nn.Conv2d(channels, channels, kernel_size=(1, 3), padding=(0, 1), groups=channels, bias=False)
        self.freq_conv = nn.Conv2d(channels, channels, kernel_size=(3, 1), padding=(1, 0), groups=channels, bias=False)
        self.point_conv = nn.Conv2d(channels, channels, kernel_size=1, bias=False)
        self.bn = nn.BatchNorm2d(channels)
        self.act = nn.PReLU()
        self.drop = nn.Dropout2d(p=dropout_rate) if dropout_rate > 0 else nn.Identity()

    def forward(self, x):
        residual = x
        out = self.norm1(x)
        out = self.time_conv(out) + self.freq_conv(out)
        out = self.point_conv(out)
        out = self.bn(out)
        out = self.act(out)
        out = self.drop(out)
        return out + residual


class TfSepNet(nn.Module):
    def __init__(self, depth=10, width=32, dropout_rate=0.2, shuffle=True, shuffle_groups=8, num_classes=2):
        super().__init__()
        self.blocks = nn.ModuleList([TfSepBlock(width, dropout_rate=dropout_rate) for _ in range(depth)])
        self.shuffle = ShuffleLayer(group=shuffle_groups) if shuffle else nn.Identity()
        self.head_conv = nn.Conv2d(width, num_classes, kernel_size=1)
        self.pool = nn.AdaptiveAvgPool2d((1, 1))

    def forward(self, x):
        for block in self.blocks:
            x = block(x)
            x = self.shuffle(x)
        x = self.head_conv(x)      # (B, num_classes, F, T)
        x = self.pool(x)           # (B, num_classes, 1, 1)
        x = x.view(x.size(0), -1)  # (B, num_classes)
        return x


class RawTFNet(nn.Module):
    """
    Full RawTFNet model (Xiao et al., 2025).
    Input: (B, 64600) raw waveform at 16 kHz.
    Output: (B, 2) logits [class 0: spoof / fake, class 1: bonafide / real].
    """
    def __init__(self, sample_rate: int = 16000):
        super().__init__()
        self.front_end = DWS_Frontend_SE(sinc_kernel_size=128, sample_rate=sample_rate)
        self.classifier = TfSepNet(depth=10, width=32, dropout_rate=0.2, shuffle=True, shuffle_groups=8, num_classes=2)

    def forward(self, x):
        feat = self.front_end(x)
        logits = self.classifier(feat)
        return logits
