import 'package:flutter_test/flutter_test.dart';
import 'package:voxshield_frontend/main.dart';

void main() {
  testWidgets('App smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const VoxShieldApp());
    expect(find.text('VoxShield'), findsOneWidget);
  });
}
