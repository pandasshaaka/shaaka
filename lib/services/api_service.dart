import 'dart:convert';
import 'package:http/http.dart' as http;
import 'cache_service.dart';

class ApiService {
  final String baseUrl;
  static const Duration _timeout = Duration(seconds: 15);
  static const int _maxRetries = 2;

  // Singleton instance for connection reuse
  static final http.Client _client = http.Client();

  ApiService({required this.baseUrl});

  Future<Map<String, dynamic>> sendOtp(String mobileNo) async {
    final uri = Uri.parse('$baseUrl/auth/send-otp');

    for (int attempt = 0; attempt <= _maxRetries; attempt++) {
      try {
        final res = await _client
            .post(
              uri,
              headers: {'Content-Type': 'application/json'},
              body: jsonEncode({'mobile_no': mobileNo}),
            )
            .timeout(_timeout);

        if (res.statusCode >= 400) {
          final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
          final errorDetail = errorBody['detail'] ?? 'Failed to send OTP';
          throw Exception(errorDetail);
        }

        return jsonDecode(res.body) as Map<String, dynamic>;
      } catch (e) {
        if (attempt == _maxRetries) {
          throw Exception(
            'Failed to send OTP: ${e.toString().replaceAll('Exception: ', '')}',
          );
        }
        await Future.delayed(Duration(milliseconds: 100 * (attempt + 1)));
      }
    }

    throw Exception('Failed to send OTP after $_maxRetries retries');
  }

  Future<Map<String, dynamic>> register(Map<String, dynamic> data) async {
    final uri = Uri.parse('$baseUrl/auth/register');

    for (int attempt = 0; attempt <= _maxRetries; attempt++) {
      try {
        final res = await _client
            .post(
              uri,
              headers: {'Content-Type': 'application/json'},
              body: jsonEncode(data),
            )
            .timeout(_timeout);

        if (res.statusCode >= 400) {
          final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
          final errorDetail = errorBody['detail'] ?? 'Registration failed';
          throw Exception(errorDetail);
        }

        return jsonDecode(res.body) as Map<String, dynamic>;
      } catch (e) {
        if (attempt == _maxRetries) {
          throw Exception(
            'Registration failed: ${e.toString().replaceAll('Exception: ', '')}',
          );
        }
        await Future.delayed(Duration(milliseconds: 100 * (attempt + 1)));
      }
    }

    throw Exception('Registration failed after $_maxRetries retries');
  }

  Future<Map<String, dynamic>> login(String mobileNo, String password) async {
    final uri = Uri.parse('$baseUrl/auth/login');

    for (int attempt = 0; attempt <= _maxRetries; attempt++) {
      try {
        final res = await _client
            .post(
              uri,
              headers: {'Content-Type': 'application/json'},
              body: jsonEncode({'mobile_no': mobileNo, 'password': password}),
            )
            .timeout(_timeout);

        if (res.statusCode >= 400) {
          final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
          final errorDetail = errorBody['detail'] ?? 'Login failed';
          throw Exception(errorDetail);
        }

        return jsonDecode(res.body) as Map<String, dynamic>;
      } catch (e) {
        if (attempt == _maxRetries || e is! http.ClientException) {
          throw Exception(
            'Login failed: ${e.toString().replaceAll('Exception: ', '')}',
          );
        }
        // Wait before retry (exponential backoff)
        await Future.delayed(Duration(milliseconds: 100 * (attempt + 1)));
      }
    }

    throw Exception('Login failed after $_maxRetries retries');
  }

  Future<Map<String, dynamic>> getProfile(String token) async {
    // Check cache first
    final cacheKey = 'profile_$token';
    final cachedData = CacheService.get(cacheKey);
    if (cachedData != null) {
      return cachedData;
    }

    final uri = Uri.parse('$baseUrl/user/me');

    for (int attempt = 0; attempt <= _maxRetries; attempt++) {
      try {
        final res = await _client
            .get(
              uri,
              headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer $token',
              },
            )
            .timeout(_timeout);

        if (res.statusCode >= 400) {
          final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
          final errorDetail = errorBody['detail'] ?? 'Failed to load profile';
          throw Exception(errorDetail);
        }

        final result = jsonDecode(res.body) as Map<String, dynamic>;
        // Cache the result
        CacheService.set(cacheKey, result);
        return result;
      } catch (e) {
        if (attempt == _maxRetries) {
          throw Exception(
            'Failed to load profile: ${e.toString().replaceAll('Exception: ', '')}',
          );
        }
        await Future.delayed(Duration(milliseconds: 100 * (attempt + 1)));
      }
    }

    throw Exception('Failed to load profile after $_maxRetries retries');
  }

  Future<Map<String, dynamic>> updateProfile(
    String token,
    Map<String, dynamic> profileData,
  ) async {
    final uri = Uri.parse('$baseUrl/user/update-profile');

    for (int attempt = 0; attempt <= _maxRetries; attempt++) {
      try {
        final res = await _client
            .post(
              uri,
              headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer $token',
              },
              body: jsonEncode(profileData),
            )
            .timeout(_timeout);

        if (res.statusCode >= 400) {
          final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
          final errorDetail = errorBody['detail'] ?? 'Failed to update profile';
          throw Exception(errorDetail);
        }

        final result = jsonDecode(res.body) as Map<String, dynamic>;
        // Clear cache after update
        CacheService.remove('profile_$token');
        return result;
      } catch (e) {
        if (attempt == _maxRetries) {
          throw Exception(
            'Failed to update profile: ${e.toString().replaceAll('Exception: ', '')}',
          );
        }
        await Future.delayed(Duration(milliseconds: 100 * (attempt + 1)));
      }
    }

    throw Exception('Failed to update profile after $_maxRetries retries');
  }

  Future<Map<String, dynamic>> reverseGeocode(
    double latitude,
    double longitude,
  ) async {
    final uri = Uri.parse('$baseUrl/geocode/reverse');
    final res = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'latitude': latitude, 'longitude': longitude}),
    );

    if (res.statusCode >= 400) {
      // Handle error response
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      final errorDetail = errorBody['detail'] ?? 'Failed to reverse geocode';
      throw Exception(errorDetail);
    }

    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  // Fallback geocoding using Nominatim (OpenStreetMap)
  Future<Map<String, dynamic>> fallbackReverseGeocode(
    double latitude,
    double longitude,
  ) async {
    try {
      // Use Nominatim API for reverse geocoding
      final uri = Uri.parse(
        'https://nominatim.openstreetmap.org/reverse?format=json&lat=$latitude&lon=$longitude&addressdetails=1',
      );

      final res = await http.get(
        uri,
        headers: {'User-Agent': 'ShaakaApp/1.0', 'Accept': 'application/json'},
      );

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body) as Map<String, dynamic>;
        final address = data['address'] as Map<String, dynamic>?;

        if (address != null) {
          // Build address line with landmark/place information
          String addressLine = '';

          // Priority order for address components (most specific to least specific)
          if (address['house_number'] != null) {
            addressLine += address['house_number'] + ' ';
          }
          if (address['road'] != null) {
            addressLine += address['road'];
          } else if (address['pedestrian'] != null) {
            addressLine += address['pedestrian'];
          } else if (address['footway'] != null) {
            addressLine += address['footway'];
          } else if (address['cycleway'] != null) {
            addressLine += address['cycleway'];
          }

          // If no street info, try landmarks and places
          if (addressLine.isEmpty) {
            if (address['amenity'] != null) {
              addressLine = address['amenity'];
            } else if (address['shop'] != null) {
              addressLine = address['shop'];
            } else if (address['building'] != null &&
                address['building'] != 'yes') {
              addressLine = address['building'];
            } else if (address['place'] != null) {
              addressLine = address['place'];
            } else if (address['suburb'] != null) {
              addressLine = address['suburb'];
            } else if (address['neighbourhood'] != null) {
              addressLine = address['neighbourhood'];
            } else if (address['quarter'] != null) {
              addressLine = address['quarter'];
            } else if (address['hamlet'] != null) {
              addressLine = address['hamlet'];
            } else if (address['isolated_dwelling'] != null) {
              addressLine = address['isolated_dwelling'];
            }
          }

          // Clean up the address line
          addressLine = addressLine.trim();

          return {
            'address_line': addressLine,
            'city':
                address['city'] ?? address['town'] ?? address['village'] ?? '',
            'state': address['state'] ?? '',
            'country': address['country'] ?? '',
            'pincode': address['postcode'] ?? '',
          };
        }
      }

      throw Exception('No address data found');
    } catch (e) {
      throw Exception('Failed to fetch address: $e');
    }
  }
}
