import 'dart:convert';
import 'package:http/http.dart' as http;
import 'cache_service.dart';

class ApiService {
  final String baseUrl;
  static const Duration _timeout = Duration(seconds: 60);
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

  Future<List<dynamic>> getCategories() async {
    final uri = Uri.parse('$baseUrl/market/categories');
    final res = await _client.get(uri).timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to load categories');
    }
    return jsonDecode(res.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> createCategory(String name) async {
    final uri = Uri.parse('$baseUrl/market/categories');
    final res = await _client
        .post(uri, headers: {'Content-Type': 'application/json'}, body: jsonEncode({'name': name}))
        .timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to create category');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> getStores({String? ownerId}) async {
    final uri = Uri.parse(ownerId == null ? '$baseUrl/market/stores' : '$baseUrl/market/stores?owner_id=$ownerId');
    final res = await _client.get(uri).timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to load stores');
    }
    return jsonDecode(res.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> createStore(String token, Map<String, dynamic> data) async {
    final uri = Uri.parse('$baseUrl/market/stores');
    final res = await _client
        .post(uri, headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer $token'}, body: jsonEncode(data))
        .timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to create store');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> getProducts({String? storeId, String? categoryId}) async {
    final params = <String, String>{};
    if (storeId != null) params['store_id'] = storeId;
    if (categoryId != null) params['category_id'] = categoryId;
    final uri = Uri.parse('$baseUrl/market/products').replace(queryParameters: params.isEmpty ? null : params);
    final res = await _client.get(uri).timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to load products');
    }
    return jsonDecode(res.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> createProduct(Map<String, dynamic> data) async {
    final uri = Uri.parse('$baseUrl/market/products');
    final res = await _client
        .post(uri, headers: {'Content-Type': 'application/json'}, body: jsonEncode(data))
        .timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to create product');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getCart(String token) async {
    final uri = Uri.parse('$baseUrl/market/cart');
    final res = await _client.get(uri, headers: {'Authorization': 'Bearer $token'}).timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to load cart');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> addToCart(String token, String productId, int quantity) async {
    final uri = Uri.parse('$baseUrl/market/cart/items');
    final res = await _client
        .post(uri, headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer $token'}, body: jsonEncode({'product_id': productId, 'quantity': quantity}))
        .timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to add to cart');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> removeCartItem(String token, String itemId) async {
    final uri = Uri.parse('$baseUrl/market/cart/items/$itemId');
    final res = await _client.delete(uri, headers: {'Authorization': 'Bearer $token'}).timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to remove cart item');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> createOrder(String token, String deliveryAddress) async {
    final uri = Uri.parse('$baseUrl/market/orders');
    final res = await _client
        .post(uri, headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer $token'}, body: jsonEncode({'delivery_address': deliveryAddress}))
        .timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to create order');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> getOrders(String token) async {
    final uri = Uri.parse('$baseUrl/market/orders');
    final res = await _client.get(uri, headers: {'Authorization': 'Bearer $token'}).timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to load orders');
    }
    return jsonDecode(res.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> createPayment(Map<String, dynamic> data) async {
    final uri = Uri.parse('$baseUrl/market/payments');
    final res = await _client
        .post(uri, headers: {'Content-Type': 'application/json'}, body: jsonEncode(data))
        .timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to create payment');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> createReview(String token, Map<String, dynamic> data) async {
    final uri = Uri.parse('$baseUrl/market/reviews');
    final res = await _client
        .post(uri, headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer $token'}, body: jsonEncode(data))
        .timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to create review');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> listReviews(String productId) async {
    final uri = Uri.parse('$baseUrl/market/reviews?product_id=$productId');
    final res = await _client.get(uri).timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to load reviews');
    }
    return jsonDecode(res.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> createDonation(String token, Map<String, dynamic> data) async {
    final uri = Uri.parse('$baseUrl/community/donations');
    final res = await _client
        .post(uri, headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer $token'}, body: jsonEncode(data))
        .timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to create donation');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> listDonations({String? status}) async {
    final uri = Uri.parse(status == null ? '$baseUrl/community/donations' : '$baseUrl/community/donations?status=$status');
    final res = await _client.get(uri).timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to load donations');
    }
    return jsonDecode(res.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> updateDonationStatus(String donationId, String status) async {
    final uri = Uri.parse('$baseUrl/community/donations/$donationId/status');
    final res = await _client
        .patch(uri, headers: {'Content-Type': 'application/json'}, body: jsonEncode({'status': status}))
        .timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to update donation');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> createDeliveryPartner(String token, Map<String, dynamic> data) async {
    final uri = Uri.parse('$baseUrl/community/delivery-partners');
    final res = await _client
        .post(uri, headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer $token'}, body: jsonEncode(data))
        .timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to create partner');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> listDeliveryPartners({bool? available}) async {
    final uri = Uri.parse(available == null ? '$baseUrl/community/delivery-partners' : '$baseUrl/community/delivery-partners?available=$available');
    final res = await _client.get(uri).timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to load partners');
    }
    return jsonDecode(res.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> createDeliveryAssignment(Map<String, dynamic> data) async {
    final uri = Uri.parse('$baseUrl/community/delivery-assignments');
    final res = await _client
        .post(uri, headers: {'Content-Type': 'application/json'}, body: jsonEncode(data))
        .timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to create assignment');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> listDeliveryAssignments({String? deliveryPartnerId}) async {
    final uri = Uri.parse(deliveryPartnerId == null ? '$baseUrl/community/delivery-assignments' : '$baseUrl/community/delivery-assignments?delivery_partner_id=$deliveryPartnerId');
    final res = await _client.get(uri).timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to load assignments');
    }
    return jsonDecode(res.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> createNotification(String userId, String title, String message) async {
    final uri = Uri.parse('$baseUrl/community/notifications');
    final res = await _client
        .post(uri, headers: {'Content-Type': 'application/json'}, body: jsonEncode({'user_id': userId, 'title': title, 'message': message}))
        .timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to create notification');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> listNotifications(String userId) async {
    final uri = Uri.parse('$baseUrl/community/notifications?user_id=$userId');
    final res = await _client.get(uri).timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to load notifications');
    }
    return jsonDecode(res.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> markNotificationRead(String notificationId) async {
    final uri = Uri.parse('$baseUrl/community/notifications/$notificationId/mark-read');
    final res = await _client.post(uri).timeout(_timeout);
    if (res.statusCode >= 400) {
      final errorBody = jsonDecode(res.body) as Map<String, dynamic>;
      throw Exception(errorBody['detail'] ?? 'Failed to mark notification');
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
