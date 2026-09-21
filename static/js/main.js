document.addEventListener("DOMContentLoaded", () => {

    // ═══════════════════════════════════════════════
    // 0. Mobile Drawer & Sidebar Toggle
    // ═══════════════════════════════════════════════
    const sidebar = document.getElementById("sidebar");
    const mobileMenuBtn = document.getElementById("mobileMenuBtn");
    const sidebarCloseBtn = document.getElementById("sidebarCloseBtn");
    const sidebarOverlay = document.getElementById("sidebarOverlay");

    function openSidebar() {
        if (sidebar) sidebar.classList.add("open");
        if (sidebarOverlay) sidebarOverlay.classList.add("active");
        document.body.style.overflow = "hidden"; // Prevent background scrolling
    }

    function closeSidebar() {
        if (sidebar) sidebar.classList.remove("open");
        if (sidebarOverlay) sidebarOverlay.classList.remove("active");
        document.body.style.overflow = "";
    }

    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener("click", openSidebar);
    }

    if (sidebarCloseBtn) {
        sidebarCloseBtn.addEventListener("click", closeSidebar);
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener("click", closeSidebar);
    }

    // Close drawer when pressing Escape
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") closeSidebar();
    });

    // Close drawer when clicking any link inside sidebar
    document.querySelectorAll(".nav-links a").forEach(link => {
        link.addEventListener("click", () => {
            if (window.innerWidth <= 900) {
                closeSidebar();
            }
        });
    });

    // ═══════════════════════════════════════════════
    // 1. Image Upload — Drag & Drop + Preview
    // ═══════════════════════════════════════════════
    const uploadBox = document.querySelector(".image-upload-box");
    const fileInput = document.getElementById("image-input");
    const previewImg = document.getElementById("preview-img");
    const uploadText = document.getElementById("upload-text");

    if (uploadBox && fileInput) {
        ['dragenter', 'dragover'].forEach(evt => {
            uploadBox.addEventListener(evt, (e) => {
                e.preventDefault();
                uploadBox.style.borderColor = 'var(--primary)';
                uploadBox.style.background = 'rgba(124, 58, 237, 0.1)';
            });
        });

        ['dragleave', 'drop'].forEach(evt => {
            uploadBox.addEventListener(evt, (e) => {
                e.preventDefault();
                uploadBox.style.borderColor = '';
                uploadBox.style.background = '';
            });
        });

        uploadBox.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                handleFile(files[0]);
            }
        });

        fileInput.addEventListener("change", (e) => {
            if (e.target.files.length > 0) handleFile(e.target.files[0]);
        });
    }

    function handleFile(file) {
        if (!file || !file.type.startsWith('image/')) return;
        const reader = new FileReader();
        reader.onload = (evt) => {
            if (previewImg) {
                previewImg.src = evt.target.result;
                previewImg.style.display = "block";
            }
            if (uploadText) {
                uploadText.innerHTML = `<i class="fa-solid fa-check-circle" style="color:var(--success)"></i> ${file.name}`;
            }
        };
        reader.readAsDataURL(file);
    }

    // ═══════════════════════════════════════════════
    // 2. Animated Counters for Stats
    // ═══════════════════════════════════════════════
    const counters = document.querySelectorAll('.counter, .counter-float');
    counters.forEach(counter => {
        const target = parseFloat(counter.getAttribute('data-target') || '0');
        const isFloat = counter.classList.contains('counter-float');
        const duration = 900;
        const startTime = performance.now();

        function updateCount(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const current = target * easeOut;

            if (isFloat) {
                counter.innerText = current.toFixed(2);
            } else {
                counter.innerText = Math.floor(current).toLocaleString();
            }

            if (progress < 1) {
                requestAnimationFrame(updateCount);
            } else {
                counter.innerText = isFloat ? target.toFixed(2) : target.toLocaleString();
            }
        }
        requestAnimationFrame(updateCount);
    });

    // ═══════════════════════════════════════════════
    // 3. Table Live Search
    // ═══════════════════════════════════════════════
    const searchInput = document.getElementById("table-search");
    if (searchInput) {
        searchInput.addEventListener("input", () => {
            const q = searchInput.value.toLowerCase().trim();
            document.querySelectorAll("#accounts-table tbody tr").forEach(row => {
                const match = row.innerText.toLowerCase().includes(q);
                row.style.display = match ? "" : "none";
                if (match) row.style.animation = "fadeIn 0.25s ease";
            });
        });
    }

    // ═══════════════════════════════════════════════
    // 4. Toast Notification System
    // ═══════════════════════════════════════════════
    window.showToast = function(msg, type = 'success') {
        const container = document.getElementById('toastContainer');
        if (!container) return;
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<i class="fa-solid fa-${type === 'success' ? 'circle-check' : 'circle-xmark'}"></i> ${msg}`;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 3200);
    };

    // ═══════════════════════════════════════════════
    // 5. Confirm Delete with Toast Feedback
    // ═══════════════════════════════════════════════
    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const confirmed = confirm('هل أنت متأكد من الحذف؟');
            if (!confirmed) {
                e.preventDefault();
                return;
            }
            showToast('تم الحذف بنجاح', 'success');
        });
    });

    // ═══════════════════════════════════════════════
    // 6. Form Submit Feedback
    // ═══════════════════════════════════════════════
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', () => {
            const btn = form.querySelector('.btn-submit');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> جاري الحفظ...';
            }
        });
    });

    // ═══════════════════════════════════════════════
    // 7. Orders Filter Functionality
    // ═══════════════════════════════════════════════
    window.filterOrders = function(status, btn) {
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        if (btn) btn.classList.add('active');

        const rows = document.querySelectorAll('#orders-table tbody tr');
        rows.forEach(row => {
            const rowStatus = row.getAttribute('data-status');
            if (status === 'all' || rowStatus === status) {
                row.style.display = '';
                row.style.animation = 'fadeIn 0.25s ease';
            } else {
                row.style.display = 'none';
            }
        });
    };

});