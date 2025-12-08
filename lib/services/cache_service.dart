class CacheService {
  static final Map<String, CacheEntry> _cache = {};
  static const Duration _defaultExpiry = Duration(minutes: 15);

  static void set(String key, dynamic data, {Duration? expiry}) {
    _cache[key] = CacheEntry(
      data: data,
      expiry: DateTime.now().add(expiry ?? _defaultExpiry),
    );
  }

  static dynamic get(String key) {
    final entry = _cache[key];
    if (entry == null) return null;

    if (DateTime.now().isAfter(entry.expiry)) {
      _cache.remove(key);
      return null;
    }

    return entry.data;
  }

  static void remove(String key) {
    _cache.remove(key);
  }

  static void clear() {
    _cache.clear();
  }

  static bool has(String key) {
    return get(key) != null;
  }
}

class CacheEntry {
  final dynamic data;
  final DateTime expiry;

  CacheEntry({required this.data, required this.expiry});
}
