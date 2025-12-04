class TokenStorage {
  static String? _token;
  static Map<String, dynamic>? _userData;
  
  static void setToken(String token) {
    _token = token;
  }
  
  static String? getToken() {
    return _token;
  }
  
  static void setUserData(Map<String, dynamic> userData) {
    _userData = userData;
  }
  
  static Map<String, dynamic>? getUserData() {
    return _userData;
  }
  
  static void clear() {
    _token = null;
    _userData = null;
  }
}