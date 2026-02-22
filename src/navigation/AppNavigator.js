/**
 * src/navigation/AppNavigator.js
 *
 * Tab navigator (Home / History) with a shared stack for modal screens
 * (Scanner, ManualEntry, TestMode, Details).
 */
import React from 'react';
import { Text, StyleSheet } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import HomeScreen from '../screens/HomeScreen';
import HistoryScreen from '../screens/HistoryScreen';
import ScannerScreen from '../screens/ScannerScreen';
import ManualEntryScreen from '../screens/ManualEntryScreen';
import TestModeScreen from '../screens/TestModeScreen';
import DetailsScreen from '../screens/DetailsScreen';

import { COLORS } from '../constants/theme';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

/**
 * Home tab + the action screens that push on top of it.
 */
function HomeStack({ scannerProps }) {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="HomeMain">
        {(props) => (
          <HomeScreen
            {...props}
            route={{
              ...props.route,
              params: {
                loading: scannerProps.loading,
                itemCount: scannerProps.itemCount,
              },
            }}
          />
        )}
      </Stack.Screen>
      <Stack.Screen name="Scanner">
        {(props) => (
          <ScannerScreen
            {...props}
            route={{
              ...props.route,
              params: {
                processBarcode: scannerProps.processBarcode,
                cancelScan: scannerProps.cancelScan,
                scanned: scannerProps.scanned,
                markScanned: scannerProps.markScanned,
                resetScanned: scannerProps.resetScanned,
                countdown: scannerProps.countdown,
                loading: scannerProps.loading,
              },
            }}
          />
        )}
      </Stack.Screen>
      <Stack.Screen name="Manual">
        {(props) => (
          <ManualEntryScreen
            {...props}
            route={{
              ...props.route,
              params: {
                processBarcode: scannerProps.processBarcode,
              },
            }}
          />
        )}
      </Stack.Screen>
      <Stack.Screen name="TestMode">
        {(props) => (
          <TestModeScreen
            {...props}
            route={{
              ...props.route,
              params: {
                processBarcode: scannerProps.processBarcode,
              },
            }}
          />
        )}
      </Stack.Screen>
      <Stack.Screen name="Details" component={DetailsScreen} />
    </Stack.Navigator>
  );
}

/**
 * History tab with its own stack (so Details can push on top).
 */
function HistoryStack({ scannedItems }) {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="HistoryMain">
        {(props) => (
          <HistoryScreen
            {...props}
            route={{
              ...props.route,
              params: { scannedItems },
            }}
          />
        )}
      </Stack.Screen>
      <Stack.Screen name="Details" component={DetailsScreen} />
    </Stack.Navigator>
  );
}

/**
 * Root TabNavigator.
 */
export default function AppNavigator({ scannerProps, scannedItems }) {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarStyle: styles.tabBar,
        tabBarActiveTintColor: COLORS.primary,
        tabBarInactiveTintColor: COLORS.textSecondary,
      }}
    >
      <Tab.Screen
        name="Home"
        options={{
          tabBarIcon: () => <Text style={styles.tabIcon}>🏠</Text>,
          tabBarLabel: 'Home',
        }}
      >
        {() => <HomeStack scannerProps={scannerProps} />}
      </Tab.Screen>

      <Tab.Screen
        name="History"
        options={{
          tabBarIcon: () => <Text style={styles.tabIcon}>📋</Text>,
          tabBarLabel: `History (${scannedItems.length})`,
        }}
      >
        {() => <HistoryStack scannedItems={scannedItems} />}
      </Tab.Screen>
    </Tab.Navigator>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: COLORS.surface,
    borderTopWidth: 2,
    borderTopColor: COLORS.primary,
    paddingBottom: 4,
    height: 60,
  },
  tabIcon: {
    fontSize: 20,
  },
});
