/* ==========================================================================
   USER INTERFACE LOGIC
   Handles modals, navigation, editor interactions, and toast notifications.
   ========================================================================== */

/* --- UI HELPERS --- */

/**
 * MM:SS Session Timer logic.
 * Updates the clock in the nav bar every second.
 */
function initSessionTimer() {
    const clock = document.getElementById("sessionClock");
    if (!clock) return;

    setInterval(() => {
        // startTime is defined globally in main.js
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const mins = Math.floor(elapsed / 60).toString().padStart(2, '0');
        const secs = (elapsed % 60).toString().padStart(2, '0');
        clock.innerText = `${mins}:${secs}`;
    }, 1000);
}

/**
 * Scroll Progress Bar and Back-to-Top visibility.
 * Visual feedback for how much content is left.
 */
function initScrollTracker() {
    const bar = document.getElementById("scrollBar");
    const btt = document.getElementById("backToTop");

    window.addEventListener('scroll', () => {
        const winScroll = document.documentElement.scrollTop;
        const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const scrolled = (winScroll / height) * 100;

        if (bar) bar.style.width = scrolled + "%";
        if (btt) btt.style.display = (winScroll > 600) ? "flex" : "none";
    });

    if (btt) {
        btt.onclick = () => window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

/**
 * Switches categories and triggers a feed reload.
 * Used by the category "pill" buttons in the header.
 */
function filterPosts(category) {
    currentCategory = category;
    currentOffset = 0;
    isFetching = false; // Reset lock to allow new fetches

    // Reset visual active state on buttons
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));

    const activeBtn = document.getElementById(`nav-${category}`);
    if (activeBtn) activeBtn.classList.add('active');

    const feed = document.getElementById('blogFeed');
    if (feed) {
        feed.innerHTML = ''; // Clear old posts
        if (typeof loadPosts === 'function') {
            loadPosts(); // Defined in api.js
        }
    }
}

/* --- VIEW MANAGEMENT (SPA) --- */

function showCreate() {
    document.getElementById('view-feed').style.display = 'none';
    document.getElementById('feed-nav').style.display = 'none';
    document.getElementById('view-create').style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showFeed() {
    document.getElementById('view-feed').style.display = 'block';
    document.getElementById('feed-nav').style.display = 'flex';
    document.getElementById('view-create').style.display = 'none';

    // Refresh the feed when returning
    filterPosts(currentCategory);
}


/* --- MODALS & DROPDOWNS --- */

function toggleDropdown() {
    document.getElementById("myDropdown").classList.toggle("show");
}

function openAIModal() {
    document.getElementById('aiModal').style.display = 'block';
}

function closeAIModal() {
    document.getElementById('aiModal').style.display = 'none';
    document.getElementById('aiPromptInput').value = '';
}

function openReportModal(postId) {
    reportingPostId = postId; // Global variable (main.js)
    const modal = document.getElementById('reportModal');
    if (modal) modal.style.display = 'block';
}

function closeReportModal() {
    reportingPostId = null;
    const modal = document.getElementById('reportModal');
    if (modal) modal.style.display = 'none';
}


/* --- WYSIWYG EDITOR LOGIC --- */

/**
 * Executes a formatting command on the contenteditable div.
 * Replaces the old 'insertFormat' text-based approach.
 * @param {string} command - The command (bold, italic, etc.)
 * @param {string} value - Optional value (e.g., for links or colors)
 */
function execCmd(command, value = null) {
    document.execCommand(command, false, value);
    // Keep focus inside the editor so the user can keep typing
    document.getElementById('postContent').focus();
}

/**
 * Prompts user for a URL and creates a hyperlink.
 */
function insertLink() {
    const url = prompt("Enter the URL:", "https://");
    if (url) {
        execCmd('createLink', url);
    }
}


/* --- AI & BACKEND INTERACTIONS --- */

/**
 * Sends a prompt to the AI endpoint and populates the editor with the draft.
 * Converts the AI's Markdown response into HTML for the WYSIWYG editor.
 */
async function submitAIPrompt() {
    const promptInput = document.getElementById('aiPromptInput');
    const promptText = promptInput.value.trim();
    const loader = document.getElementById('aiLoading');

    if (!promptText) {
        showToast("⚠️ Please enter a topic first.");
        return;
    }

    loader.style.display = 'block';

    try {
        const response = await fetch(`${API_URL}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic: promptText })
        });

        const data = await response.json();

        if (response.ok) {
            // Fill Metadata Fields
            document.getElementById('postTitle').value = data.title || "";
            document.getElementById('postHashtags').value = data.hashtags || "";

            // Fill Content: Convert AI Markdown (**bold**) to HTML (<b>bold</b>)
            // This is crucial because our editor is HTML-based now.
            if (typeof marked !== 'undefined' && data.content) {
                document.getElementById('postContent').innerHTML = marked.parse(data.content);
            } else {
                document.getElementById('postContent').innerText = data.content || "";
            }

            // Auto-Select Category
            if (data.category) {
                const categorySelect = document.getElementById('postCategory');
                categorySelect.value = data.category;

                // Visual Flash Effect
                categorySelect.style.borderColor = "var(--accent)";
                setTimeout(() => { categorySelect.style.borderColor = "var(--border-light)"; }, 1000);
            }

            showToast("✨ Magic Generated!");
            closeAIModal();
        } else {
            showToast(`❌ ${data.error || "AI Generation failed"}`);
        }
    } catch (error) {
        console.error("AI Fetch Error:", error);
        showToast("❌ Server connection error");
    } finally {
        loader.style.display = 'none';
    }
}

/**
 * Submits a community report for a specific post.
 */
async function submitReport() {
    if (!reportingPostId) return; // Global variable set when opening modal

    const reason = document.getElementById('reportReason').value;

    try {
        const res = await fetch(`${API_URL}/report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ post_id: reportingPostId, reason: reason })
        });

        // 1. Always try to parse the JSON response first
        const data = await res.json();

        if (res.ok) {
            showToast("🚩 Content reported. Thank you.");
            closeReportModal();

            // Visual feedback: Dim the reported card
            const card = document.querySelector(`.post-card[data-id="${reportingPostId}"]`);
            if (card) card.style.opacity = '0.3';
        } else {
            // 2. SHOW THE REAL ERROR MESSAGE FROM THE SERVER
            // This will now say "Too many requests" or "Server Error" instead of lying to you.
            showToast(`⚠️ ${data.message || "Error submitting report"}`);
        }
    } catch (e) {
        console.error("Report Error:", e);
        showToast("❌ Connection error");
    }
}


/* --- COMMENTS & SOCIAL --- */

/**
 * Toggles comment section visibility and fetches comments if opening.
 */
async function toggleComments(postId) {
    const section = document.getElementById(`comments-${postId}`);

    if (section.style.display === 'none') {
        section.style.display = 'block';
        const list = document.getElementById(`comment-list-${postId}`);
        list.innerHTML = '<p style="font-size:0.8rem; color:#888;">Loading...</p>';

        try {
            const res = await fetch(`${API_URL}/comments?post_id=${postId}`);
            const comments = await res.json();

            list.innerHTML = comments.length ? '' : '<p style="font-size:0.8rem; color:#888;">No comments yet.</p>';

            comments.forEach(c => {
                const div = document.createElement('div');
                div.className = 'comment-item';
                div.innerHTML = `<span class="comment-date">${c.date.split(' ')[0]}</span><p>${c.content}</p>`;
                list.appendChild(div);
            });
        } catch (e) {
            list.innerHTML = '<p style="color:red">Error loading comments.</p>';
        }
    } else {
        section.style.display = 'none';
    }
}

async function postComment(postId) {
    const input = document.getElementById(`input-${postId}`);
    const content = input.value.trim();
    if (!content) return;

    try {
        const res = await fetch(`${API_URL}/comments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ post_id: postId, content: content })
        });

        const data = await res.json();

        if (res.ok) {
            input.value = '';

            // Update the badge count immediately
            const badge = document.getElementById(`comment-count-${postId}`);
            if (badge) {
                const currentCount = parseInt(badge.innerText) || 0;
                badge.innerText = currentCount + 1;
            }

            // Reload comments to show the new one
            toggleComments(postId);
            showToast("💬 Comment added");
        } else {
            showToast(`⛔ ${data.reason || "Error"}`);
        }
    } catch (e) {
        showToast("❌ Connection error");
    }
}

/**
 * Generic Toast Notification Trigger
 */
function showToast(message) {
    const x = document.getElementById("toast");
    x.innerText = message;
    x.className = "show";
    setTimeout(() => { x.className = ""; }, 3000);
}

/**
 * Copies the current page URL to clipboard.
 */
function sharePost(title) {
    const dummy = document.createElement('input');
    document.body.appendChild(dummy);
    dummy.value = window.location.href; // In real app, this would be a specific post permalink
    dummy.select();
    document.execCommand('copy');
    document.body.removeChild(dummy);
    showToast(`🔗 Link copied: ${title}`);
}