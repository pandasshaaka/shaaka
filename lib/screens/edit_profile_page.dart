import 'package:flutter/material.dart';
import 'dart:convert';
import '../services/api_service.dart';
import 'map_picker_page.dart';
import 'dart:io';
import 'package:image_picker/image_picker.dart';

class EditProfilePage extends StatefulWidget {
  final Map<String, dynamic> userData;
  final String token;

  const EditProfilePage({
    super.key,
    required this.userData,
    required this.token,
  });

  @override
  State<EditProfilePage> createState() => _EditProfilePageState();
}

class _EditProfilePageState extends State<EditProfilePage> {
  final _formKey = GlobalKey<FormState>();
  final _api = ApiService(baseUrl: 'https://shaaka.onrender.com');

  late TextEditingController _fullNameController;
  late TextEditingController _mobileController;
  late TextEditingController _genderController;
  late TextEditingController _addressController;
  late TextEditingController _cityController;
  late TextEditingController _stateController;
  late TextEditingController _countryController;
  late TextEditingController _pincodeController;

  File? _photoFile;
  String? _photoBase64;
  String? _photoMimeType;
  double? _latitude;
  double? _longitude;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _initializeControllers();
  }

  void _initializeControllers() {
    _fullNameController = TextEditingController(
      text: widget.userData['full_name'] ?? '',
    );
    _mobileController = TextEditingController(
      text: widget.userData['mobile_no'] ?? '',
    );
    _genderController = TextEditingController(
      text: widget.userData['gender'] ?? '',
    );
    _addressController = TextEditingController(
      text: widget.userData['address_line'] ?? '',
    );
    _cityController = TextEditingController(
      text: widget.userData['city'] ?? '',
    );
    _stateController = TextEditingController(
      text: widget.userData['state'] ?? '',
    );
    _countryController = TextEditingController(
      text: widget.userData['country'] ?? '',
    );
    _pincodeController = TextEditingController(
      text: widget.userData['pincode'] ?? '',
    );

    _latitude = widget.userData['latitude']?.toDouble();
    _longitude = widget.userData['longitude']?.toDouble();
  }

  @override
  void dispose() {
    _fullNameController.dispose();
    _mobileController.dispose();
    _genderController.dispose();
    _addressController.dispose();
    _cityController.dispose();
    _stateController.dispose();
    _countryController.dispose();
    _pincodeController.dispose();
    super.dispose();
  }

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: ImageSource.gallery);

    if (pickedFile != null) {
      setState(() {
        _photoFile = File(pickedFile.path);
      });

      // Convert to base64
      final bytes = await _photoFile!.readAsBytes();
      setState(() {
        _photoBase64 = base64Encode(bytes);
        _photoMimeType =
            'image/jpeg'; // Default to JPEG, you can detect actual type
      });
    }
  }

  Future<void> _selectLocation() async {
    final result = await Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const MapPickerPage()),
    );

    if (result != null && result is Map<String, double>) {
      setState(() {
        _latitude = result['latitude'];
        _longitude = result['longitude'];
      });
    }
  }

  Future<void> _saveProfile() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _saving = true;
    });

    try {
      final profileData = {
        'full_name': _fullNameController.text.trim(),
        'mobile_no': _mobileController.text.trim(),
        'gender': _genderController.text.trim(),
        'address_line': _addressController.text.trim(),
        'city': _cityController.text.trim(),
        'state': _stateController.text.trim(),
        'country': _countryController.text.trim(),
        'pincode': _pincodeController.text.trim(),
      };

      // Add photo data if available
      if (_photoBase64 != null && _photoMimeType != null) {
        profileData['profile_photo_data'] = _photoBase64!;
        profileData['profile_photo_mime_type'] = _photoMimeType!;
      }

      final response = await _api.updateProfile(widget.token, profileData);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Profile updated successfully!')),
        );
        Navigator.pop(context, response); // Return updated data
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Error: ${e.toString()}')));
      }
    } finally {
      if (mounted) {
        setState(() {
          _saving = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Edit Profile'),
        backgroundColor: Colors.deepPurple,
        foregroundColor: Colors.white,
        actions: [
          TextButton(
            onPressed: _saving ? null : _saveProfile,
            child: _saving
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Text('Save', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
      body: Form(
        key: _formKey,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Profile Photo
              Center(
                child: Stack(
                  children: [
                    Container(
                      width: 120,
                      height: 120,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(color: Colors.deepPurple, width: 3),
                      ),
                      child: ClipOval(
                        child: _photoFile != null
                            ? Image.file(_photoFile!, fit: BoxFit.cover)
                            : widget.userData['profile_photo_data'] != null
                            ? Image.memory(
                                base64Decode(
                                  widget.userData['profile_photo_data'],
                                ),
                                fit: BoxFit.cover,
                              )
                            : widget.userData['profile_photo_url'] != null
                            ? Image.network(
                                'https://shaaka.onrender.com${widget.userData['profile_photo_url']}',
                                fit: BoxFit.cover,
                              )
                            : Container(
                                color: Colors.grey[200],
                                child: const Icon(
                                  Icons.person,
                                  size: 60,
                                  color: Colors.grey,
                                ),
                              ),
                      ),
                    ),
                    Positioned(
                      bottom: 0,
                      right: 0,
                      child: Container(
                        decoration: BoxDecoration(
                          color: Colors.deepPurple,
                          shape: BoxShape.circle,
                        ),
                        child: IconButton(
                          icon: const Icon(
                            Icons.camera_alt,
                            color: Colors.white,
                          ),
                          onPressed: _pickImage,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 32),

              // Full Name
              TextFormField(
                controller: _fullNameController,
                decoration: const InputDecoration(
                  labelText: 'Full Name',
                  prefixIcon: Icon(Icons.person),
                ),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Please enter your full name';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),

              // Mobile Number
              TextFormField(
                controller: _mobileController,
                decoration: const InputDecoration(
                  labelText: 'Mobile Number',
                  prefixIcon: Icon(Icons.phone),
                ),
                keyboardType: TextInputType.phone,
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Please enter your mobile number';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),

              // Gender
              TextFormField(
                controller: _genderController,
                decoration: const InputDecoration(
                  labelText: 'Gender',
                  prefixIcon: Icon(Icons.transgender),
                ),
              ),
              const SizedBox(height: 16),

              // Address
              TextFormField(
                controller: _addressController,
                decoration: const InputDecoration(
                  labelText: 'Address',
                  prefixIcon: Icon(Icons.home),
                ),
                maxLines: 2,
              ),
              const SizedBox(height: 16),

              // City
              TextFormField(
                controller: _cityController,
                decoration: const InputDecoration(
                  labelText: 'City',
                  prefixIcon: Icon(Icons.location_city),
                ),
              ),
              const SizedBox(height: 16),

              // State
              TextFormField(
                controller: _stateController,
                decoration: const InputDecoration(
                  labelText: 'State',
                  prefixIcon: Icon(Icons.map),
                ),
              ),
              const SizedBox(height: 16),

              // Country
              TextFormField(
                controller: _countryController,
                decoration: const InputDecoration(
                  labelText: 'Country',
                  prefixIcon: Icon(Icons.public),
                ),
              ),
              const SizedBox(height: 16),

              // Pincode
              TextFormField(
                controller: _pincodeController,
                decoration: const InputDecoration(
                  labelText: 'Pincode',
                  prefixIcon: Icon(Icons.pin_drop),
                ),
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: 16),

              // Location Selection
              Card(
                child: ListTile(
                  leading: const Icon(
                    Icons.location_on,
                    color: Colors.deepPurple,
                  ),
                  title: Text(
                    _latitude != null && _longitude != null
                        ? 'Location: ${(_latitude!).toStringAsFixed(6)}, ${(_longitude!).toStringAsFixed(6)}'
                        : 'No location selected',
                  ),
                  trailing: TextButton(
                    onPressed: _selectLocation,
                    child: const Text('Select on Map'),
                  ),
                ),
              ),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }
}
