import 'dart:convert';

import 'package:http/http.dart' as http;

class OperatorClient {
  OperatorClient({required this.baseUrl, http.Client? client})
      : _client = client ?? http.Client();

  final String baseUrl;
  final http.Client _client;

  Uri _uri(String path) => Uri.parse('$baseUrl$path');

  Future<Map<String, dynamic>> status() async {
    return _map(await _client.get(_uri('/status')));
  }

  Future<List<dynamic>> bots() async {
    return _list(await _client.get(_uri('/bots')));
  }

  Future<Map<String, dynamic>> readiness() async {
    return _map(await _client.get(_uri('/readiness')));
  }

  Future<Map<String, dynamic>> setBotEnabled(String id, bool enabled) async {
    final action = enabled ? 'enable' : 'disable';
    return _map(await _client.post(_uri('/bots/$id/$action')));
  }

  Future<Map<String, dynamic>> pauseAll({
    String reason = 'operator pause',
  }) async {
    return _map(
      await _client.post(
        _uri('/pause'),
        headers: {'content-type': 'application/json'},
        body: jsonEncode({'reason': reason}),
      ),
    );
  }

  Map<String, dynamic> _map(http.Response response) {
    _check(response);
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  List<dynamic> _list(http.Response response) {
    _check(response);
    return jsonDecode(response.body) as List<dynamic>;
  }

  void _check(http.Response response) {
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw StateError('Operator API ${response.statusCode}');
    }
  }
}
