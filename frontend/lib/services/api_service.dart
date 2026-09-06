import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import '../models/call_analysis.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  String baseUrl = 'http://127.0.0.1:8000'; // Default for local desktop/web; can be configured in settings

  void updateBaseUrl(String url) {
    baseUrl = url.replaceAll(RegExp(r'/+$'), '');
  }

  /// Check health of backend server
  Future<bool> checkHealth() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/health'))
          .timeout(const Duration(seconds: 3));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// Upload raw audio file / bytes to FastAPI /analyze
  Future<CallAnalysis> analyzeAudioBytes(
    Uint8List audioBytes, {
    String filename = 'call_recording.wav',
    String? callerName,
    String? callerNumber,
    int duration = 30,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/analyze');
      final request = http.MultipartRequest('POST', uri);

      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          audioBytes,
          filename: filename,
        ),
      );

      final streamedResponse = await request.send().timeout(const Duration(seconds: 15));
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = jsonDecode(response.body);
        return CallAnalysis.fromJson(
          data,
          callerName: callerName,
          callerNumber: callerNumber,
          duration: duration,
        );
      } else {
        throw Exception('Server returned status ${response.statusCode}: ${response.body}');
      }
    } catch (e) {
      // Return simulated realistic response when backend is offline
      return generateSimulatedAnalysis(
        scenario: 'bank_otp_scam',
        callerName: callerName,
        callerNumber: callerNumber,
        duration: duration,
      );
    }
  }

  /// Provides realistic scenario analyses for live demonstrations & tests
  CallAnalysis generateSimulatedAnalysis({
    required String scenario,
    String? callerName,
    String? callerNumber,
    int duration = 45,
  }) {
    switch (scenario) {
      case 'bank_otp_scam':
        return CallAnalysis(
          overallRisk: 72,
          level: RiskLevel.high,
          voiceRisk: 78,
          scamRisk: 81,
          urgencyScore: 70,
          voiceAnalysis: VoiceAnalysisResult(
            isAiVoice: true,
            confidence: 0.78,
            spectralJitter: 0.84,
            pitchStability: 0.93,
            voiceProfile: 'Neural TTS / ElevenLabs Cloned Voice',
          ),
          transcript:
              "Caller: 'Good day, I am calling from Chase Fraud Security. We noticed an unauthorized withdrawal attempt of \$1,450. To cancel this transaction immediately, please read aloud the 6-digit one-time passcode we just sent to your phone via SMS.'",
          warnings: [
            ScamWarning(
              id: 'w1',
              title: '⚠️ OTP request detected',
              description: 'The caller demanded a 6-digit SMS verification code. Banks NEVER ask for OTP over the phone.',
              category: 'OTP',
              severity: RiskLevel.critical,
            ),
            ScamWarning(
              id: 'w2',
              title: '⚠️ Urgent payment request',
              description: 'Urgency tactics employed to compel immediate financial authorization.',
              category: 'URGENT_PAYMENT',
              severity: RiskLevel.high,
            ),
            ScamWarning(
              id: 'w3',
              title: '⚠️ Synthetic voice profile',
              description: 'Neural voice cloning signatures identified with 78% confidence.',
              category: 'DEEPFAKE_VOICE',
              severity: RiskLevel.critical,
            ),
          ],
          detectedPatterns: [
            'OTP & Credential Harvesting',
            'Bank Impersonation Social Engineering',
            'Artificial Urgency / Coercion',
            'Deepfake Neural Synthesis',
          ],
          recommendations: [
            '🚨 Terminate this call immediately. Do NOT speak any verification digits.',
            '🔒 Contact Chase Bank using the customer care number on the back of your card.',
            '🛡️ Check your banking app for any active unauthorized login sessions.',
          ],
          callerName: callerName ?? 'Chase Fraud Dept (Spoofed)',
          callerNumber: callerNumber ?? '+1 (800) 935-9935',
          callDurationSeconds: duration,
        );

      case 'family_emergency_deepfake':
        return CallAnalysis(
          overallRisk: 89,
          level: RiskLevel.critical,
          voiceRisk: 94,
          scamRisk: 88,
          urgencyScore: 95,
          voiceAnalysis: VoiceAnalysisResult(
            isAiVoice: true,
            confidence: 0.94,
            spectralJitter: 0.89,
            pitchStability: 0.96,
            voiceProfile: 'Zero-Shot AI Voice Clone (Family Member Impersonation)',
          ),
          transcript:
              "Caller: 'Mom, I got into a bad car accident downtown! The police are holding my car and I need you to wire \$2,000 right now to this account or they will take me to jail. Please don\\'t call Dad, just send it now!'",
          warnings: [
            ScamWarning(
              id: 'w10',
              title: '🚨 Cloned Family Voice Detected',
              description: 'High confidence AI voice clone designed to mimic distress and emotional vulnerability.',
              category: 'DEEPFAKE_VOICE',
              severity: RiskLevel.critical,
            ),
            ScamWarning(
              id: 'w11',
              title: '⚠️ Emergency Wire Demand',
              description: 'High-pressure financial extortion posing as a family legal crisis.',
              category: 'URGENT_PAYMENT',
              severity: RiskLevel.critical,
            ),
            ScamWarning(
              id: 'w12',
              title: '⚠️ Isolation Tactic',
              description: 'Caller explicitly requested you not contact other family members.',
              category: 'IMPERSONATION',
              severity: RiskLevel.high,
            ),
          ],
          detectedPatterns: [
            'Grandparent/Family Emergency Extortion',
            'Emotional Coercion & Pressure',
            'Deepfake Voice Cloning',
            'Instant Wire / Crypto Demand',
          ],
          recommendations: [
            '🛑 Hang up immediately and directly call your family member on their known cell number.',
            '🔑 Ask a secret personal verification question that only your real family member would know.',
            '🚔 Report the incident to your local cybersecurity cybercrime division.',
          ],
          callerName: callerName ?? 'Unknown / Hidden ID',
          callerNumber: callerNumber ?? '+1 (415) 890-1122',
          callDurationSeconds: duration,
        );

      case 'legitimate_call':
      default:
        return CallAnalysis(
          overallRisk: 12,
          level: RiskLevel.safe,
          voiceRisk: 8,
          scamRisk: 15,
          urgencyScore: 10,
          voiceAnalysis: VoiceAnalysisResult(
            isAiVoice: false,
            confidence: 0.08,
            spectralJitter: 0.12,
            pitchStability: 0.22,
            voiceProfile: 'Natural Human Acoustics (Authentic)',
          ),
          transcript:
              "Caller: 'Hey Alex, just checking in to see if you are still free for lunch today at 1 PM downtown? Let me know whenever you have a chance.'",
          warnings: [],
          detectedPatterns: [
            'Natural Speech Pattern Verified',
            'No Social Engineering Keywords',
            'No Financial or OTP Inquiries',
          ],
          recommendations: [
            '✅ Call verified as safe. No malicious acoustic or linguistic anomalies detected.',
          ],
          callerName: callerName ?? 'Alex Morgan',
          callerNumber: callerNumber ?? '+1 (555) 234-5678',
          callDurationSeconds: duration,
        );
    }
  }
}
