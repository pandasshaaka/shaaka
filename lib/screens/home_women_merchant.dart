import 'package:flutter/material.dart';
import '../services/token_storage.dart';

class HomeWomenMerchantPage extends StatelessWidget {
  const HomeWomenMerchantPage({super.key});

  void _navigateToPage(BuildContext context, String route) {
    Navigator.pushNamed(context, route);
  }

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
          leading: IconButton(
            icon: const Icon(Icons.menu),
            onPressed: () => Scaffold.of(context).openDrawer(),
          ),
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
        drawer: Drawer(
          child: ListView(
            padding: EdgeInsets.zero,
            children: [
              const DrawerHeader(
                decoration: BoxDecoration(color: Colors.deepPurple),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    Icon(Icons.storefront, size: 48, color: Colors.white),
                    SizedBox(height: 8),
                    Text(
                      'Women Merchant Menu',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
              ListTile(
                leading: const Icon(Icons.store_mall_directory),
                title: const Text('Browse Stores'),
                onTap: () => _navigateToPage(context, '/store'),
              ),
              ListTile(
                leading: const Icon(Icons.shopping_cart),
                title: const Text('Shopping Cart'),
                onTap: () => _navigateToPage(context, '/cart'),
              ),
              ListTile(
                leading: const Icon(Icons.volunteer_activism),
                title: const Text('Donations'),
                onTap: () => _navigateToPage(context, '/donation'),
              ),
              ListTile(
                leading: const Icon(Icons.shopping_bag),
                title: const Text('Your Orders'),
                onTap: () => _navigateToPage(context, '/orders'),
              ),
              const Divider(),
              ListTile(
                leading: const Icon(Icons.home),
                title: const Text('Dashboard'),
                onTap: () => Navigator.pop(context),
              ),
            ],
          ),
        ),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.storefront, size: 64, color: Colors.deepPurple),
              const SizedBox(height: 16),
              const Text(
                'Welcome to Women Merchant Dashboard',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              const Text(
                'Empowering women entrepreneurs',
                style: TextStyle(fontSize: 16, color: Colors.grey),
              ),
              const SizedBox(height: 32),
              Wrap(
                spacing: 16,
                runSpacing: 16,
                alignment: WrapAlignment.center,
                children: [
                  ElevatedButton.icon(
                    onPressed: () => _navigateToPage(context, '/store'),
                    icon: const Icon(Icons.store_mall_directory),
                    label: const Text('Browse Stores'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.deepPurple,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 20,
                        vertical: 12,
                      ),
                    ),
                  ),
                  ElevatedButton.icon(
                    onPressed: () => _navigateToPage(context, '/cart'),
                    icon: const Icon(Icons.shopping_cart),
                    label: const Text('Shopping Cart'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.deepPurple,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 20,
                        vertical: 12,
                      ),
                    ),
                  ),
                  ElevatedButton.icon(
                    onPressed: () => _navigateToPage(context, '/donation'),
                    icon: const Icon(Icons.volunteer_activism),
                    label: const Text('Donations'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.deepPurple,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 20,
                        vertical: 12,
                      ),
                    ),
                  ),
                  ElevatedButton.icon(
                    onPressed: () => _navigateToPage(context, '/orders'),
                    icon: const Icon(Icons.shopping_bag),
                    label: const Text('Your Orders'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.deepPurple,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 20,
                        vertical: 12,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
