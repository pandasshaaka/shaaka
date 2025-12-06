import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  final String baseUrl;
  ApiService({required this.baseUrl});

  Future<Map<String, dynamic>> sendOtp(String mobileNo) async {
    try {
      final uri = Uri.parse('$baseUrl/auth/send-otp');
      final res = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'mobile_no': mobileNo}),
      );

      if (res.statusCode >= 400) {
        // Handle error response
        final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
        final errorDetail = errorBody['detail'] ?? 'Failed to send OTP';
        throw Exception(errorDetail);
      }

      return jsonDecode(res.body) as Map<String, dynamic>;
    } catch (e) {
      throw Exception('Network error: ${e.toString()}');
    }
  }

  Future<Map<String, dynamic>> register(Map<String, dynamic> data) async {
    final uri = Uri.parse('$baseUrl/auth/register');
    final res = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(data),
    );

    if (res.statusCode >= 400) {
      // Handle error response
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      final errorDetail = errorBody['detail'] ?? 'Registration failed';
      throw Exception(errorDetail);
    }

    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> login(String mobileNo, String password) async {
    final uri = Uri.parse('$baseUrl/auth/login');
    final res = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'mobile_no': mobileNo, 'password': password}),
    );

    if (res.statusCode >= 400) {
      // Handle error response
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      final errorDetail = errorBody['detail'] ?? 'Login failed';
      throw Exception(errorDetail);
    }

    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getProfile(String token) async {
    final uri = Uri.parse('$baseUrl/user/me');
    final res = await http.get(
      uri,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (res.statusCode >= 400) {
      // Handle error response
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      final errorDetail = errorBody['detail'] ?? 'Failed to load profile';
      throw Exception(errorDetail);
    }

    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> updateProfile(String token, Map<String, dynamic> profileData) async {
    final uri = Uri.parse('$baseUrl/user/update-profile');
    final res = await http.post(
      uri,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode(profileData),
    );

    if (res.statusCode >= 400) {
      // Handle error response
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      final errorDetail = errorBody['detail'] ?? 'Failed to update profile';
      throw Exception(errorDetail);
    }

    return jsonDecode(res.body) as Map<String, dynamic>;
  }
}
