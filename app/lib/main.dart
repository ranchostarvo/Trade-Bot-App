import 'package:flutter/material.dart';

import 'operator_client.dart';

void main() {
  const api = String.fromEnvironment(
    'OPERATOR_API_URL',
    defaultValue: 'http://127.0.0.1:8000',
  );
  runApp(TradeBotApp(client: OperatorClient(baseUrl: api)));
}

class TradeBotApp extends StatelessWidget {
  const TradeBotApp({super.key, required this.client});

  final OperatorClient client;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Trade Bot Operator',
      theme: ThemeData(useMaterial3: true),
      home: Dashboard(client: client),
    );
  }
}

class Dashboard extends StatefulWidget {
  const Dashboard({super.key, required this.client});

  final OperatorClient client;

  @override
  State<Dashboard> createState() => _DashboardState();
}

class _DashboardState extends State<Dashboard> {
  Map<String, dynamic>? status;
  Map<String, dynamic>? readiness;
  List<dynamic> bots = const [];
  String? error;
  bool busy = true;

  @override
  void initState() {
    super.initState();
    refresh();
  }

  Future<void> refresh() async {
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final values = await Future.wait([
        widget.client.status(),
        widget.client.readiness(),
        widget.client.bots(),
      ]);
      if (!mounted) return;
      setState(() {
        status = values[0] as Map<String, dynamic>;
        readiness = values[1] as Map<String, dynamic>;
        bots = values[2] as List<dynamic>;
      });
    } catch (exception) {
      if (mounted) setState(() => error = exception.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> toggleBot(Map<String, dynamic> bot, bool enabled) async {
    setState(() => busy = true);
    try {
      await widget.client.setBotEnabled(bot['bot_id'] as String, enabled);
      await refresh();
    } catch (exception) {
      if (mounted) {
        setState(() {
          error = exception.toString();
          busy = false;
        });
      }
    }
  }

  Future<void> pauseAll() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Pause all bots?'),
        content: const Text(
          'This engages the global safety pause and disables configured bots.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Pause all'),
          ),
        ],
      ),
    );
    if (confirmed == true) {
      await widget.client.pauseAll();
      await refresh();
    }
  }

  @override
  Widget build(BuildContext context) {
    final runtime =
        status?['runtime'] as Map<String, dynamic>? ?? const {};
    final summary = status?['bots'] as Map<String, dynamic>? ?? const {};
    final ready = readiness?['ready'] == true;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Paper Trading Operator'),
        actions: [
          IconButton(
            onPressed: busy ? null : refresh,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: refresh,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (busy) const LinearProgressIndicator(),
            if (error != null)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text('Connection error: $error'),
                ),
              ),
            Card(
              child: ListTile(
                leading: Icon(ready ? Icons.verified_user : Icons.gpp_bad),
                title: Text(
                  ready ? 'Paper readiness: GO' : 'Paper readiness: NO-GO',
                ),
                subtitle: Text(
                  "Runtime ready: ${runtime['ready'] == true} • "
                  "Enabled bots: ${summary['enabled'] ?? 0}/"
                  "${summary['configured'] ?? 0}",
                ),
              ),
            ),
            const SizedBox(height: 8),
            FilledButton.tonalIcon(
              onPressed: busy ? null : pauseAll,
              icon: const Icon(Icons.pause_circle),
              label: const Text('GLOBAL PAUSE'),
            ),
            const SizedBox(height: 16),
            Text('Bots', style: Theme.of(context).textTheme.headlineSmall),
            ...bots.map((raw) {
              final bot = raw as Map<String, dynamic>;
              return Card(
                child: SwitchListTile(
                  value: bot['enabled'] == true,
                  onChanged: busy ? null : (value) => toggleBot(bot, value),
                  title: Text("${bot['bot_id']} • ${bot['symbol']}"),
                  subtitle: Text(
                    "${bot['asset_class']} • ${bot['risk_profile']}",
                  ),
                ),
              );
            }),
            const SizedBox(height: 16),
            const Card(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Text(
                  'Safety mode\n'
                  'Live trading controls are intentionally absent. '
                  'Orders cannot be submitted directly from this console. '
                  'All execution remains behind the guarded runtime.',
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
