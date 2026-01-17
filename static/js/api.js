/* ==========================================================================
   API COMMUNICATION LAYER
   Handles all network requests: Fetching feeds, Uploading posts, and Tracking interactions.
   ========================================================================== */

/**
 * Fetches posts based on the current active category and pagination offset.
 * * Logic:
 * 1. Checks 'isFetching' to prevent duplicate requests if the user scrolls too fast.
 * 2. Toggles the loading skeleton animation.
 * 3. Hits different endpoints for 'Trending' vs standard 'Category' feeds.
 * 4. Updates the global offset for infinite scrolling.
 */
async function loadPosts() {
    // STOP: If a request is already running, don't start another one.
    if (isFetching) return;

    const feed = document.getElementById('blogFeed');
    const loader = document.getElementById('loading-animation');

    isFetching = true; // Lock the function
    if (loader) loader.style.display = 'block';

    // ROUTING: 'Trending' has its own dedicated endpoint with a unique algorithm.
    // All other categories use the standard query-based endpoint.
    let url = currentCategory === 'trending'
        ? `${API_URL}/posts/trending`
        : `${API_URL}/posts?category=${currentCategory}&offset=${currentOffset}&limit=${POSTS_PER_PAGE}`;

    try {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);

        const posts = await res.json();

        // EMPTY STATE: If we get 0 posts on the very first load (offset 0), show a message.
        if (posts.length === 0 && currentOffset === 0) {
            feed.innerHTML = '<p style="text-align:center; color:#ccc; margin-top:40px;">No posts found.</p>';
            isFetching = false;
            return;
        }

        // Pass data to main.js to create the HTML cards
        renderPosts(posts);
        currentOffset += posts.length;

        // PAGINATION LOGIC:
        // If we received fewer posts than requested (e.g., asked for 5, got 3),
        // we've reached the end of the database. Stop fetching.
        // Trending is usually a fixed list (Top 10), so we disable scrolling there too.
        isFetching = (currentCategory === 'trending' || posts.length < POSTS_PER_PAGE);

    } catch (error) {
        console.error("Fetch Error:", error);
        isFetching = false;
    } finally {
        if (loader) loader.style.display = 'none';
    }
}

/**
 * Handles the creation of a new post.
 * * Key Features:
 * - Supports Multipart Form Data (required for Image Uploads).
 * - Grabs HTML content from the WYSIWYG editor.
 * - Disables the publish button to prevent double-clicks.
 */
async function handlePost() {
    // Grab inputs
    const title = document.getElementById('postTitle').value.trim();

    // IMPORTANT: We use .innerHTML because the editor is a ContentEditable DIV, not a textarea.
    const content = document.getElementById('postContent').innerHTML;

    const category = document.getElementById('postCategory').value;
    const hashtags = document.getElementById('postHashtags').value.trim();

    // Check for the optional image file
    const imageInput = document.getElementById('postImage');
    const imageFile = imageInput ? imageInput.files[0] : null;

    const btn = document.getElementById('btnPublish');

    // Basic Validation
    if (!title || !category || !content) {
        showToast("⚠️ Please fill in all required fields");
        return;
    }

    btn.disabled = true; // Prevent spam clicking

    // PAYLOAD CONSTRUCTION:
    // We use FormData instead of JSON because we might be sending a binary image file.
    const formData = new FormData();
    formData.append('title', title);
    formData.append('content', content);
    formData.append('category', category);
    formData.append('hashtags', hashtags);
    if (imageFile) formData.append('image', imageFile);

    try {
        // Note: When using FormData, fetch automatically sets the correct Content-Type with boundaries.
        // Do NOT manually set 'Content-Type': 'multipart/form-data'.
        const postRes = await fetch(`${API_URL}/posts`, {
            method: 'POST',
            body: formData
        });

        if (postRes.ok) {
            showToast("✅ Post Published!");

            // CLEANUP: Reset form and return to feed
            document.getElementById('postTitle').value = '';
            document.getElementById('postContent').innerHTML = ''; // Clear rich text editor
            document.getElementById('postHashtags').value = '';
            if (imageInput) imageInput.value = '';

            // Refresh the feed to show the new post
            filterPosts('all');
            showFeed();
        } else {
            const err = await postRes.json();
            showToast(`⛔ ${err.reason || "Error saving post"}`);
        }
    } catch (e) {
        console.error("Publish Error:", e);
        showToast("❌ Server connection error");
    } finally {
        btn.disabled = false; // Re-enable button
    }
}

/**
 * Tracks unique views for analytics.
 * This is triggered by the IntersectionObserver (observers.js) when a post card
 * stays on screen for a set amount of time.
 */
async function incrementView(postId) {
    // "Fire and Forget" request - we don't need to wait for the response.
    fetch(`${API_URL}/posts/view`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ post_id: postId })
    }).catch(e => console.error("View tracking error:", e));
}

/**
 * Handles the Like button interaction.
 * Uses "Optimistic UI" - updates the heart icon immediately for instant feedback,
 * then sends the request in the background.
 */
async function toggleLike(btn, postId) {
    const icon = btn.querySelector('i');
    const countSpan = btn.querySelector('.like-count');

    // Check current state based on CSS class
    const isLiked = btn.classList.contains('liked');
    const action = isLiked ? 'remove' : 'add';

    try {
        const res = await fetch(`${API_URL}/posts/like`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ post_id: postId, action: action })
        });

        if (res.ok) {
            // OPTIMISTIC UPDATE: Toggle UI immediately
            btn.classList.toggle('liked');

            // Switch between solid (fas) and outline (far) heart icons
            icon.classList.toggle('fa-solid');
            icon.classList.toggle('fa-regular');

            // Update the number counter
            let currentLikes = parseInt(countSpan.innerText) || 0;
            countSpan.innerText = action === 'add' ? currentLikes + 1 : Math.max(0, currentLikes - 1);
        }
    } catch (e) {
        console.error("Like Error:", e);
        // Optional: Revert UI here if request fails (not implemented for simplicity)
    }
}