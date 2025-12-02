import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/file_service.dart';
import 'map_picker_page.dart';
import 'dart:io';
import 'package:image_picker/image_picker.dart';
import '../data/country_state_data.dart';

class RegisterPage extends StatefulWidget {
  const RegisterPage({super.key});
  @override
  State<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends State<RegisterPage> {
  final _formKey = GlobalKey<FormState>();
  final _fullNameController = TextEditingController();
  final _mobileController = TextEditingController();
  final _passwordController = TextEditingController();
  final _genderController = TextEditingController();
  String _category = 'Customer';
  final _addressController = TextEditingController();
  final _cityController = TextEditingController();
  final _stateController = TextEditingController();
  final _countryController = TextEditingController();
  final _pincodeController = TextEditingController();
  double? _latitude;
  double? _longitude;
  File? _photoFile;
  String? _photoUrl;
  List<String> _availableStates = [];
  final _otpController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  bool _sendingOtp = false;
  bool _registering = false;
  bool _otpSent = false;
  bool _obscurePassword = true;
  bool _obscureConfirmPassword = true;
  final _api = ApiService(baseUrl: 'http://192.168.1.106:8000');
  final _files = FileService(baseUrl: 'http://192.168.1.106:8000');

  String? _validatePassword(String? value) {
    if (value == null || value.isEmpty) {
      return 'Password is required';
    }
    if (value.length < 8) {
      return 'Password must be at least 8 characters';
    }
    if (!value.contains(RegExp(r'[A-Z]'))) {
      return 'Password must contain at least one uppercase letter';
    }
    if (!value.contains(RegExp(r'[a-z]'))) {
      return 'Password must contain at least one lowercase letter';
    }
    if (!value.contains(RegExp(r'[0-9]'))) {
      return 'Password must contain at least one number';
    }
    if (!value.contains(RegExp(r'[!@#$%^&*(),.?":{}|<>]'))) {
      return 'Password must contain at least one special character';
    }
    return null;
  }

  void _onCountrySelected(String? country) {
    setState(() {
      _countryController.text = country ?? '';
      _stateController.text = ''; // Clear state when country changes
      _availableStates = country != null
          ? CountryStateData.getStates(country)
          : [];
    });
  }

  Future<void> _sendOtp() async {
    if (_mobileController.text.trim().isEmpty) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Enter mobile number')));
      return;
    }
    setState(() => _sendingOtp = true);
    try {
      await _api.sendOtp(_mobileController.text.trim());
      if (mounted) {
        setState(() => _otpSent = true);
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('OTP sent')));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to send OTP: ${e.toString()}')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _sendingOtp = false);
      }
    }
  }

  Future<void> _register() async {
    if (!_formKey.currentState!.validate()) return;
    if (_passwordController.text != _confirmPasswordController.text) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('Passwords do not match')));
      }
      return;
    }
    if (_latitude == null || _longitude == null) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please select location on map')),
        );
      }
      return;
    }
    if (_photoFile != null && _photoUrl == null) {
      final url = await _files.uploadImage(_photoFile!);
      _photoUrl = url;
    }
    setState(() => _registering = true);
    try {
      final data = {
        'full_name': _fullNameController.text.trim(),
        'mobile_no': _mobileController.text.trim(),
        'password': _passwordController.text,
        'gender': _genderController.text.trim().isEmpty
            ? null
            : _genderController.text.trim(),
        'category': _category,
        'address_line': _addressController.text.trim().isEmpty
            ? null
            : _addressController.text.trim(),
        'city': _cityController.text.trim().isEmpty
            ? null
            : _cityController.text.trim(),
        'state': _stateController.text.trim().isEmpty
            ? null
            : _stateController.text.trim(),
        'country': _countryController.text.trim().isEmpty
            ? null
            : _countryController.text.trim(),
        'pincode': _pincodeController.text.trim().isEmpty
            ? null
            : _pincodeController.text.trim(),
        'latitude': _latitude,
        'longitude': _longitude,
        'profile_photo_url': _photoUrl,
        'otp_code': _otpController.text.trim(),
      };
      await _api.register(data);
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Registered')));
      Navigator.pushReplacementNamed(context, '/login');
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('Registration failed')));
      }
    } finally {
      if (mounted) {
        setState(() => _registering = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Register')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextFormField(
                controller: _fullNameController,
                decoration: const InputDecoration(labelText: 'Full Name'),
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? 'Required' : null,
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: _mobileController,
                      decoration: const InputDecoration(
                        labelText: 'Mobile Number',
                      ),
                      keyboardType: TextInputType.phone,
                      validator: (v) =>
                          (v == null || v.trim().isEmpty) ? 'Required' : null,
                    ),
                  ),
                  const SizedBox(width: 8),
                  ElevatedButton(
                    onPressed: _sendingOtp ? null : _sendOtp,
                    child: _sendingOtp
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text('Send OTP'),
                  ),
                ],
              ),
              if (_otpSent) ...[
                const SizedBox(height: 12),
                TextFormField(
                  controller: _otpController,
                  decoration: const InputDecoration(labelText: 'OTP'),
                  keyboardType: TextInputType.number,
                  validator: (v) =>
                      (v == null || v.trim().isEmpty) ? 'Required' : null,
                ),
              ],
              const SizedBox(height: 12),
              TextFormField(
                controller: _passwordController,
                decoration: InputDecoration(
                  labelText: 'Password',
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscurePassword
                          ? Icons.visibility
                          : Icons.visibility_off,
                    ),
                    onPressed: () =>
                        setState(() => _obscurePassword = !_obscurePassword),
                  ),
                ),
                obscureText: _obscurePassword,
                validator: (v) => _validatePassword(v),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _confirmPasswordController,
                decoration: InputDecoration(
                  labelText: 'Confirm Password',
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscureConfirmPassword
                          ? Icons.visibility
                          : Icons.visibility_off,
                    ),
                    onPressed: () => setState(
                      () => _obscureConfirmPassword = !_obscureConfirmPassword,
                    ),
                  ),
                ),
                obscureText: _obscureConfirmPassword,
                validator: (v) => (v == null || v.isEmpty) ? 'Required' : null,
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _genderController.text.isEmpty
                    ? null
                    : _genderController.text,
                items: const [
                  DropdownMenuItem(value: 'Male', child: Text('Male')),
                  DropdownMenuItem(value: 'Female', child: Text('Female')),
                  DropdownMenuItem(value: 'Other', child: Text('Other')),
                ],
                onChanged: (value) {
                  setState(() {
                    _genderController.text = value ?? '';
                  });
                },
                decoration: const InputDecoration(labelText: 'Gender'),
                hint: const Text('Select Gender'),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _category,
                items: const [
                  DropdownMenuItem(value: 'Vendor', child: Text('Vendor')),
                  DropdownMenuItem(
                    value: 'Women Merchant',
                    child: Text('Women Merchant'),
                  ),
                  DropdownMenuItem(value: 'Customer', child: Text('Customer')),
                ],
                onChanged: (v) => setState(() => _category = v ?? 'Customer'),
                decoration: const InputDecoration(labelText: 'Category'),
                validator: (v) => (v == null || v.isEmpty) ? 'Required' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _addressController,
                decoration: const InputDecoration(labelText: 'Address Line'),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _cityController,
                decoration: const InputDecoration(labelText: 'City'),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _countryController.text.isEmpty
                    ? null
                    : _countryController.text,
                items: CountryStateData.getCountries()
                    .map(
                      (country) => DropdownMenuItem(
                        value: country,
                        child: Text(country),
                      ),
                    )
                    .toList(),
                onChanged: _onCountrySelected,
                decoration: const InputDecoration(labelText: 'Country'),
                hint: const Text('Select Country'),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _stateController.text.isEmpty
                    ? null
                    : _stateController.text,
                items: _availableStates
                    .map(
                      (state) =>
                          DropdownMenuItem(value: state, child: Text(state)),
                    )
                    .toList(),
                onChanged: (value) {
                  setState(() {
                    _stateController.text = value ?? '';
                  });
                },
                decoration: const InputDecoration(labelText: 'State'),
                hint: const Text('Select State'),
                disabledHint: Text(
                  _countryController.text.isEmpty
                      ? 'Please select a country first'
                      : 'No states available',
                ),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _pincodeController,
                decoration: const InputDecoration(labelText: 'Pincode'),
                keyboardType: TextInputType.number,
                validator: (v) {
                  if (v == null || v.isEmpty) return null; // Optional field
                  if (!RegExp(r'^[0-9]+$').hasMatch(v)) {
                    return 'Pincode must contain only numbers';
                  }
                  if (v.length < 4 || v.length > 10) {
                    return 'Pincode must be 4-10 digits';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 12),
              ListTile(
                title: Text(
                  _latitude == null
                      ? 'Select Location on Map'
                      : 'Lat: ${_latitude!.toStringAsFixed(6)}, Lng: ${_longitude!.toStringAsFixed(6)}',
                ),
                trailing: const Icon(Icons.map),
                onTap: () async {
                  final result = await Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const MapPickerPage()),
                  );
                  if (result != null && mounted) {
                    _latitude = (result.latitude as double);
                    _longitude = (result.longitude as double);
                    setState(() {});
                  }
                },
              ),
              const SizedBox(height: 12),
              ListTile(
                title: Text(
                  _photoFile == null ? 'Pick Profile Photo' : 'Photo Selected',
                ),
                trailing: const Icon(Icons.photo_library),
                onTap: () async {
                  final picker = ImagePicker();
                  final xfile = await picker.pickImage(
                    source: ImageSource.gallery,
                    imageQuality: 85,
                  );
                  if (xfile != null) {
                    _photoFile = File(xfile.path);
                    setState(() {});
                  }
                },
              ),
              const SizedBox(height: 20),
              ElevatedButton(
                onPressed: _registering ? null : _register,
                child: _registering
                    ? const CircularProgressIndicator()
                    : const Text('Register'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
