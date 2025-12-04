import 'package:flutter/material.dart';
import '../services/token_storage.dart';

class HomeWomenMerchantPage extends StatelessWidget {
  const HomeWomenMerchantPage({super.key});
  
  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false, // Disable system back button
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Women Merchant Dashboard'),
          automaticallyImplyLeading: false, // Remove back button
          backgroundColor: Colors.deepPurple,
          foregroundColor: Colors.white,
          actions: [
            IconButton(
              icon: const Icon(Icons.person),
              onPressed: () {
                final token = TokenStorage.getToken();
                final userData = TokenStorage.getUserData();
                if (token != null && userData != null) {
                  Navigator.pushNamed(
                    context,
                    '/profile',
                    arguments: {
                      'userId': userData['mobile_no'],
                      'token': token,
                    },
                  );
                } else {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Please login again')),
                  );
                }
              },
            ),
          ],
        ),
        body: const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.storefront, size: 64, color: Colors.deepPurple),
              SizedBox(height: 16),
              Text(
                'Welcome to Women Merchant Dashboard',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text(
                'Empowering women entrepreneurs',
                style: TextStyle(fontSize: 16, color: Colors.grey),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
