import 'dart:convert';
import 'package:http/http.dart' as http;

class OperatorClient {
  OperatorClient({required this.baseUrl, http.Client? client})\n      : _client = client ?? http.Client();
  final String baseUrl;
  final http.Client _client;
  Uri _uri(String path) => Uri.parse('$baseUrl$path');

  Future<Map<String, dynamic>> status() async =>\n      _map(await _client.get(_uri('/status')));
  Future<List<dynamic>> bots() async =>\n      _list(await _client.get(_uri('/bots')));
  Future<Map<String, dynamic>> readiness() async =>\n      _map(await _client.get(_uri('/readiness')));
  Future<Map<String, dynamic>> setBotEnabled(String id, bool enabled) async {
    final action = enabled ? 'enable' : 'disable';
    return _map(await _client.post(_uri('/bots/$id/$action')));
  }
  Future<Map<String, dynamic>> pauseAll({String reason = 'operator pause'}) async =>
      _map(await _client.post(_uri('/pause'), headers: {'content-type': 'application/json'}, body: jsonEncode({'reason': reason})));

  Map<String, dynamic> _map(http.Response r) { _check(r); return jsonDecode(r.body) as Map<String, dynamic>; }
  List<dynamic> _list(http.Response r) { _check(r); return jsonDecode(r.body) as List<dynamic>; }
  void _check(http.Response r) {
    if (r.statusCode < 200 || r.statusCode >= 300) throw StateError('Operator API ${r.statusCode}');
  }
}
