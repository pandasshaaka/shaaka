import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/token_storage.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});
  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _mobileController = TextEditingController();
  final _passwordController = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  bool _loading = false;
  final _api = ApiService(baseUrl: 'https://shaaka.onrender.com');

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);

    // Show loading indicator with progress message
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
            const SizedBox(width: 12),
            const Text('Connecting to server...'),
          ],
        ),
        duration: const Duration(seconds: 30),
        backgroundColor: Colors.blue,
      ),
    );

    try {
      final res = await _api.login(
        _mobileController.text.trim(),
        _passwordController.text,
      );
      final category = res['category'] as String?;
      final token = res['access_token'] as String?;

      if (!mounted) return;

      // Clear loading snackbar
      if (mounted) {
        ScaffoldMessenger.of(context).clearSnackBars();
      }

      // Store token and user data
      if (token != null) {
        TokenStorage.setToken(token);
        TokenStorage.setUserData({
          'mobile_no': _mobileController.text.trim(),
          'category': category,
        });
      }

      // Show success message with better UX
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Login successful! Welcome back...'),
            backgroundColor: Colors.green,
            duration: Duration(seconds: 1),
          ),
        );
      }

      // Add a small delay for better user experience
      await Future.delayed(const Duration(milliseconds: 300));

      if (!mounted) return;

      if (category == 'Vendor') {
        Navigator.pushNamedAndRemoveUntil(
          context,
          '/home_vendor',
          (route) => false,
        );
      } else if (category == 'Women Merchant') {
        Navigator.pushNamedAndRemoveUntil(
          context,
          '/home_women',
          (route) => false,
        );
      } else {
        Navigator.pushNamedAndRemoveUntil(
          context,
          '/home_customer',
          (route) => false,
        );
      }
    } catch (e) {
      if (mounted) {
        // Clear loading snackbar
        ScaffoldMessenger.of(context).clearSnackBars();

        String errorMessage = e.toString().replaceAll('Exception: ', '');

        // Provide more user-friendly error messages
        if (errorMessage.contains('timeout')) {
          errorMessage =
              'Server is taking too long to respond. Please try again.';
        } else if (errorMessage.contains('Network error')) {
          errorMessage =
              'Network connection issue. Please check your internet.';
        } else if (errorMessage.contains('401') ||
            errorMessage.toLowerCase().contains('invalid')) {
          errorMessage = 'Invalid mobile number or password.';
        }

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Login failed: $errorMessage'),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 4),
            action: SnackBarAction(
              label: 'RETRY',
              textColor: Colors.white,
              onPressed: _login,
            ),
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Login')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextFormField(
                controller: _mobileController,
                decoration: const InputDecoration(labelText: 'Mobile Number'),
                keyboardType: TextInputType.phone,
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? 'Required' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _passwordController,
                decoration: const InputDecoration(labelText: 'Password'),
                obscureText: true,
                validator: (v) => (v == null || v.isEmpty) ? 'Required' : null,
              ),
              const SizedBox(height: 20),
              ElevatedButton(
                onPressed: _loading ? null : _login,
                child: _loading
                    ? const CircularProgressIndicator()
                    : const Text('Login'),
              ),
              const SizedBox(height: 12),
              TextButton(
                onPressed: () => Navigator.pushNamed(context, '/register'),
                child: const Text('Create account'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
