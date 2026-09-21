document.addEventListener("DOMContentLoaded", () => {

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
    // 2. Table Live Search
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
    // 3. Toast Notification System
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
    // 4. Confirm Delete with Toast Feedback
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
    // 5. Form Submit Feedback
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
    // 6. Row Hover Micro Animation
    // ═══════════════════════════════════════════════
    document.querySelectorAll('tbody tr').forEach(row => {
        row.style.transition = 'background 0.2s ease';
    });

});