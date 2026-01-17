/* ==========================================================================
   MAIN ENTRY POINT & GLOBAL STATE
   This file acts as the "Central Nervous System" of the frontend.
   It holds the global variables and boots up the application subsystems.
   ========================================================================== */

/* --- CONFIGURATION & CONSTANTS --- */
const API_URL = '/api';
const POSTS_PER_PAGE = 5;

/* --- GLOBAL STATE MANAGEMENT --- */
// We define these here so they are accessible by api.js, ui.js, and observers.js
let currentCategory = 'all';  // The active tab (e.g., 'Tech', 'Trending')
let currentOffset = 0;        // Pagination cursor (how many posts we have loaded)
let isFetching = false;       // Lock to prevent double-fetching on scroll
let reportingPostId = null;   // Tracks which post is currently being reported

// Session Tracking: Start the clock for the "Time Online" counter
const startTime = Date.now();

// PERSISTENCE:
// We verify which posts the user has already "read" (scrolled past) using LocalStorage.
// This allows us to dim them visually even if the user refreshes the page.
let seenPosts = JSON.parse(localStorage.getItem('seenPosts')) || [];


/* ==========================================================================
   SYSTEM INITIALIZATION
   Boots up the app once the HTML is fully parsed.
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    console.log("🚀 Smart Blog System Initializing...");

    try {
        // 1. BOOTSTRAP UI COMPONENTS
        // We use 'typeof' checks to ensure the other script files (ui.js, observers.js)
        // loaded correctly. This prevents the whole app from crashing if one file fails.
        if (typeof initSessionTimer === 'function') {
            initSessionTimer(); // Starts the clock in the nav bar
        }

        if (typeof initScrollTracker === 'function') {
            initScrollTracker(); // Update the progress bar at the top
        }

        // 2. INITIALIZE SCROLL OBSERVERS
        // This is the engine behind "Infinite Scroll".
        if (typeof initInfiniteScroll === 'function') {
            initInfiniteScroll();
        } else {
            console.error("❌ Critical: initInfiniteScroll not found. Check observers.js.");
        }

        // 3. INITIAL DATA FETCH
        // We add a tiny delay (200ms) to let the browser finish layout calculations.
        // This ensures the IntersectionObserver doesn't accidentally trigger twice on load.
        setTimeout(() => {
            console.log("📦 Performing initial fetch for 'all' category...");
            if (typeof filterPosts === 'function') {
                filterPosts('all'); // This calls loadPosts() in api.js
            }
        }, 200);

    } catch (error) {
        console.error("⚠️ System initialization failed:", error);
    }
});


/* ==========================================================================
   UTILITY & MAINTENANCE
   Helper functions to keep the browser environment clean.
   ========================================================================== */

/**
 * Cleanup Routine:
 * If the user reads thousands of posts, the 'seenPosts' array in LocalStorage
 * can get huge. We cap it at 100 recent posts to keep the browser fast.
 */
function maintainLocalStorage() {
    if (seenPosts.length > 500) {
        console.log("🧹 Garbage Collection: Cleaning up old read history...");
        // Keep only the last 100 items
        seenPosts = seenPosts.slice(-100);
        localStorage.setItem('seenPosts', JSON.stringify(seenPosts));
    }
}

// Run maintenance immediately on load
maintainLocalStorage();