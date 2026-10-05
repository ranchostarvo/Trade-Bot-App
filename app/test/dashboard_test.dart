import 'package:flutter_test/flutter_test.dart';
import 'package:trade_bot_operator/main.dart';
import 'package:trade_bot_operator/operator_client.dart';

void main() {
  testWidgets('operator console exposes no live trading control', (tester) async {
    await tester.pumpWidget(TradeBotApp(client: OperatorClient(baseUrl: 'http://127.0.0.1:1')));
    await tester.pump();
    expect(find.textContaining('Paper Trading Operator'), findsOneWidget);
    expect(find.textContaining('Submit Order'), findsNothing);
  });
}
