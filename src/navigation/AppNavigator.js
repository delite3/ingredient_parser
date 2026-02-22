/**
 * src/navigation/AppNavigator.js
 *
 * Tab navigator (Home / History) with nested stacks for modal screens.
 *
 * All shared state (scanner, history) is accessed via React Context —
 * no inline render functions, so React Navigation never remounts screens
 * due to changed function references.
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

import { useHistory } from '../context/HistoryContext';
import { COLORS } from '../constants/theme';

const Tab = createBottomTabNavigator();
const HomeStackNav = createNativeStackNavigator();
const HistoryStackNav = createNativeStackNavigator();

/**
 * Home tab + the action screens that push on top of it.
 * All screens pull data from context — no props drilling.
 */
function HomeStack() {
  return (
    <HomeStackNav.Navigator screenOptions={{ headerShown: false }}>
      <HomeStackNav.Screen name="HomeMain" component={HomeScreen} />
      <HomeStackNav.Screen name="Scanner" component={ScannerScreen} />
      <HomeStackNav.Screen name="Manual" component={ManualEntryScreen} />
      <HomeStackNav.Screen name="TestMode" component={TestModeScreen} />
      <HomeStackNav.Screen name="Details" component={DetailsScreen} />
    </HomeStackNav.Navigator>
  );
}

/**
 * History tab with its own stack (so Details can push on top).
 */
function HistoryStack() {
  return (
    <HistoryStackNav.Navigator screenOptions={{ headerShown: false }}>
      <HistoryStackNav.Screen name="HistoryMain" component={HistoryScreen} />
      <HistoryStackNav.Screen name="Details" component={DetailsScreen} />
    </HistoryStackNav.Navigator>
  );
}

/**
 * Root TabNavigator.
 */
export default function AppNavigator() {
  const { scannedItems } = useHistory();

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
        component={HomeStack}
        options={{
          tabBarIcon: () => <Text style={styles.tabIcon}>🏠</Text>,
          tabBarLabel: 'Home',
        }}
      />

      <Tab.Screen
        name="History"
        component={HistoryStack}
        options={{
          tabBarIcon: () => <Text style={styles.tabIcon}>📋</Text>,
          tabBarLabel: `History (${scannedItems.length})`,
        }}
      />
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
