/* ==========================================================================
   INTERSECTION OBSERVERS & RENDERING
   Handles visibility tracking, infinite scroll, and HTML rendering logic.
   ========================================================================== */

/**
 * Global store for active "Dwell Timers".
 * Why? If a user scrolls past a post quickly, we shouldn't mark it as 'Read'.
 * We only mark it as 'Read' if they stay on it for 2 seconds.
 * * Key: postId, Value: setTimeout ID
 */
const dwellTimers = {};

/**
 * 1. THE REVEAL OBSERVER
 * Monitors individual post cards as they enter the screen.
 * Tasks:
 * - Animation: Adds 'visible' class to trigger CSS fade-in.
 * - Analytics: Increments view count (once per session).
 * - User Habits: Tracks if a user actually reads the story (2-second dwell).
 */
const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        const postId = entry.target.dataset.id;

        if (entry.isIntersecting) {
            // A. TRIGGER ENTRANCE ANIMATION
            entry.target.classList.add('visible');

            // B. VIEW TRACKING (Fixes SQLite Database Locks)
            // Only fire the view increment endpoint if we haven't tracked this card yet.
            if (!entry.target.dataset.viewed) {
                if (typeof incrementView === 'function') {
                    incrementView(postId); // Defined in api.js
                }
                entry.target.dataset.viewed = "true"; // Mark locally as tracked
            }

            // C. START READING TIMER
            // If the user hasn't seen this post before, start the countdown.
            if (!seenPosts.includes(postId) && !dwellTimers[postId]) {
                dwellTimers[postId] = setTimeout(() => {
                    // 2 Seconds Passed: Mark as Read
                    seenPosts.push(postId);
                    localStorage.setItem('seenPosts', JSON.stringify(seenPosts));

                    // Update UI visually
                    entry.target.classList.add('is-read');
                    showToast("📖 Story Completed");

                    // Cleanup
                    delete dwellTimers[postId];
                }, 2000); // 2000ms = 2 seconds
            }
        } else {
            // D. CANCEL TIMER ON SCROLL EXIT
            // If the user scrolls away before 2 seconds, cancel the 'Read' status.
            if (dwellTimers[postId]) {
                clearTimeout(dwellTimers[postId]);
                delete dwellTimers[postId];
            }
        }
    });
}, { threshold: 0.1 }); // Trigger when 10% of the card is visible

/**
 * 2. INFINITE SCROLL OBSERVER
 * Watches the invisible footer element to load more posts.
 */
function initInfiniteScroll() {
    const trigger = document.getElementById('infinite-scroll-trigger');
    if (!trigger) return;

    const scrollObserver = new IntersectionObserver((entries) => {
        // Only load if the trigger is visible AND we aren't already loading something.
        if (entries[0].isIntersecting && !isFetching) {
            console.log("⚓ Infinite scroll triggered...");
            if (typeof loadPosts === 'function') {
                loadPosts(); // Defined in api.js
            }
        }
    }, { threshold: 0.1 });

    scrollObserver.observe(trigger);
}

/**
 * 3. RENDER LOGIC
 * Takes raw JSON data and turns it into HTML cards.
 * Now supports Markdown parsing via marked.js for Rich Text.
 * * @param {Array} posts - List of post objects from the API.
 */
function renderPosts(posts) {
    const feed = document.getElementById('blogFeed');

    posts.forEach(post => {
        const postIdStr = post.id.toString();

        // Format Date (e.g., "Jan 17")
        const dateStr = new Date(post.date).toLocaleDateString(undefined, {
            month: 'short',
            day: 'numeric'
        });

        // Check LocalStorage to see if we should gray out this post
        const isRead = seenPosts.includes(postIdStr) ? 'is-read' : '';

        // Calculate Read Time (Avg reading speed = 200 words/min)
        // Strip HTML tags for accurate word count
        const textContent = post.content.replace(/<[^>]*>/g, '');
        const wordCount = textContent.split(/\s+/).length;
        const readTimeText = Math.ceil(wordCount / 200) + ' min read';

        // --- MARKDOWN & RICH TEXT PARSING ---
        // Converts **bold**, *italic*, and <ul> lists into real HTML.
        let renderedContent = post.content;
        try {
            if (typeof marked !== 'undefined') {
                // Parse markdown, but ensure we don't double-escape existing HTML
                renderedContent = marked.parse(post.content);
            }
        } catch (e) {
            console.warn("Markdown parsing failed, falling back to raw text", e);
        }

        // --- HASHTAG FORMATTING ---
        // Turns string "#code #life" into clickable pills.
        let hashtagHtml = '';
        if (post.hashtags) {
            const tags = post.hashtags.split(' ');
            hashtagHtml = '<div class="hashtag-container">';
            tags.forEach(tag => {
                let cleanTag = tag.trim();
                if (!cleanTag) return;
                // Ensure hash prefix
                if (!cleanTag.startsWith('#')) cleanTag = '#' + cleanTag;
                hashtagHtml += `<span class="hashtag-pill">${cleanTag}</span>`;
            });
            hashtagHtml += '</div>';
        }

        const safeTitle = post.title.replace(/'/g, "\\'");

        // Create the Card Element
        const card = document.createElement('div');
        // Add 'scroll-reveal' for animation and 'is-read' for dimming
        card.className = `post-card scroll-reveal ${isRead}`;
        card.dataset.id = postIdStr;

        // Populate HTML
        card.innerHTML = `
            ${currentCategory === 'trending' ? `
                <div class="trending-badge">
                    <i class="fa-solid fa-fire"></i> Trending Score: ${Math.round(post.score || 0)}
                </div>` : ''}

            ${post.image_url ? `<img src="${post.image_url}" class="post-cover" loading="lazy">` : ''}
            
            <h3>${post.title}</h3>
            
            <div class="post-body">${renderedContent}</div>
            
            ${hashtagHtml}

            <div class="action-bar">
                <button onclick="toggleLike(this, ${post.id})" class="btn-icon" title="Like">
                    <i class="fa-regular fa-heart"></i> 
                    <span class="like-count">${post.likes || 0}</span>
                </button>
                <button onclick="toggleComments(${post.id})" class="btn-icon" title="Comments">
                    <i class="fa-regular fa-comment"></i>
                    <span class="count-badge" id="comment-count-${post.id}">${post.comment_count || 0}</span>
                </button>
                <button onclick="sharePost('${safeTitle}')" class="btn-icon" title="Copy Link">
                    <i class="fa-solid fa-share-nodes"></i>
                </button>
                
                <div class="view-count"><i class="fa-regular fa-eye"></i> ${post.views || 0}</div>
                
                <div style="margin-left:auto; display:flex; align-items:center; gap:10px;">
                    <span style="font-size:0.8rem; color:#666;">${readTimeText}</span>
                    <button onclick="openReportModal(${post.id})" class="btn-icon btn-report" title="Report Content">
                        <i class="fa-regular fa-flag"></i>
                    </button>
                </div>
            </div>

            <div id="comments-${post.id}" class="comments-section" style="display: none;">
                <div id="comment-list-${post.id}" class="comment-list"></div>
                <div class="comment-input-group">
                    <input type="text" id="input-${post.id}" placeholder="Write a comment...">
                    <button onclick="postComment(${post.id})" class="btn-comment-send">
                        <i class="fa-solid fa-paper-plane"></i>
                    </button>
                </div>
            </div>

            <div class="post-footer">
                <span class="category-tag">${post.category}</span>
                ${dateStr}
            </div>
        `;

        feed.appendChild(card);

        // Attach the Reveal Observer to this specific card
        revealObserver.observe(card);
    });
}