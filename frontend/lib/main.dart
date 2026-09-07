import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'models/call_analysis.dart';
import 'screens/history_screen.dart';
import 'screens/home_screen.dart';
import 'widgets/call_overlay.dart';
import 'services/call_monitor.dart';

@pragma("vm:entry-point")
void overlayMain() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(
    const MaterialApp(
      debugShowCheckedModeBanner: false,
      home: CallOverlayWidget(),
    ),
  );
}

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      systemNavigationBarColor: Color(0xFF0F172A),
      systemNavigationBarIconBrightness: Brightness.light,
    ),
  );
  
  // Initialize the background call listener
  CallMonitorService().initialize();
  
  runApp(const VoxShieldApp());
}

class VoxShieldApp extends StatefulWidget {
  const VoxShieldApp({super.key});

  @override
  State<VoxShieldApp> createState() => _VoxShieldAppState();
}

class _VoxShieldAppState extends State<VoxShieldApp> {
  final AppSettings _settings = AppSettings();
  int _currentIndex = 0;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'VoxShield - Real-Time Call Scam & Deepfake Protection',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0A0F1D),
        primaryColor: const Color(0xFF2563EB),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF2563EB),
          secondary: Color(0xFF38BDF8),
          surface: Color(0xFF0F172A),
          error: Color(0xFFEF4444),
        ),
        fontFamily: 'Roboto',
        useMaterial3: true,
      ),
      home: Scaffold(
        body: IndexedStack(
          index: _currentIndex,
          children: [
            HomeScreen(settings: _settings),
            const HistoryScreen(),
          ],
        ),
        bottomNavigationBar: Container(
          decoration: const BoxDecoration(
            color: Color(0xFF0F172A),
            border: Border(
              top: BorderSide(color: Color(0xFF1E293B), width: 1),
            ),
          ),
          child: BottomNavigationBar(
            currentIndex: _currentIndex,
            backgroundColor: Colors.transparent,
            elevation: 0,
            selectedItemColor: const Color(0xFF38BDF8),
            unselectedItemColor: Colors.white38,
            selectedLabelStyle: const TextStyle(fontWeight: FontWeight.w700, fontSize: 12),
            unselectedLabelStyle: const TextStyle(fontWeight: FontWeight.w500, fontSize: 11),
            onTap: (index) {
              setState(() {
                _currentIndex = index;
              });
            },
            items: const [
              BottomNavigationBarItem(
                icon: Icon(Icons.shield_rounded),
                activeIcon: Icon(Icons.shield_rounded),
                label: 'Dashboard',
              ),
              BottomNavigationBarItem(
                icon: Icon(Icons.history_rounded),
                activeIcon: Icon(Icons.history_rounded),
                label: 'Call History',
              ),
            ],
          ),
        ),
      ),
    );
  }
}
