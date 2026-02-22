/**
 * Persistent storage service using AsyncStorage.
 *
 * Stores scan history so it survives app restarts.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

const HISTORY_KEY = '@scan_history';

/**
 * Load all scanned items from persistent storage.
 * Returns an array (empty if nothing saved yet).
 */
export async function loadHistory() {
  try {
    const json = await AsyncStorage.getItem(HISTORY_KEY);
    return json ? JSON.parse(json) : [];
  } catch (error) {
    console.warn('Failed to load history:', error.message);
    return [];
  }
}

/**
 * Persist the full scanned-items array.
 */
export async function saveHistory(items) {
  try {
    await AsyncStorage.setItem(HISTORY_KEY, JSON.stringify(items));
  } catch (error) {
    console.warn('Failed to save history:', error.message);
  }
}

/**
 * Clear all saved scan history.
 */
export async function clearHistory() {
  try {
    await AsyncStorage.removeItem(HISTORY_KEY);
  } catch (error) {
    console.warn('Failed to clear history:', error.message);
  }
}
