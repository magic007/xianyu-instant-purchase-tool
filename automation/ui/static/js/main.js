document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('searchForm');
    const searchResults = document.getElementById('searchResults');
    const searchResultsTable = document.getElementById('searchResultsTable');
    const resultStats = document.getElementById('resultStats');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorMessage = document.getElementById('errorMessage');
    const clearCollectionsBtn = document.getElementById('clearCollections');
    const itemTemplate = document.getElementById('itemTemplate');
    const tableRowTemplate = document.getElementById('tableRowTemplate');
    const gridViewBtn = document.getElementById('gridViewBtn');
    const tableViewBtn = document.getElementById('tableViewBtn');
    const gridView = document.getElementById('gridView');
    const tableView = document.getElementById('tableView');
    const advancedSearchToggle = document.querySelector('[data-bs-toggle="collapse"]');
    const locationSelect = document.getElementById('location');
    
    // 视图切换
    gridViewBtn.addEventListener('click', function() {
        gridView.style.display = 'block';
        tableView.style.display = 'none';
        gridViewBtn.classList.add('active');
        tableViewBtn.classList.remove('active');
    });
    
    tableViewBtn.addEventListener('click', function() {
        gridView.style.display = 'none';
        tableView.style.display = 'block';
        gridViewBtn.classList.remove('active');
        tableViewBtn.classList.add('active');
    });
    
    // 加载地区列表
    loadLocations();
    
    // 判断是否使用高级搜索
    let useAdvancedSearch = false;
    
    // 监听高级搜索折叠状态变化
    document.getElementById('advancedSearch').addEventListener('shown.bs.collapse', function() {
        useAdvancedSearch = true;
    });
    
    document.getElementById('advancedSearch').addEventListener('hidden.bs.collapse', function() {
        useAdvancedSearch = false;
    });
    
    // 搜索事件处理
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // 显示加载指示器
        searchResults.innerHTML = '';
        searchResultsTable.innerHTML = '';
        resultStats.textContent = '';
        loadingIndicator.classList.remove('d-none');
        errorMessage.classList.add('d-none');
        
        // 获取表单数据
        const formData = new FormData(searchForm);
        
        // 处理复选框
        if (document.getElementById('isAttention').checked) {
            formData.set('is_attention', 'true');
        } else {
            formData.set('is_attention', 'false');
        }
        
        // 使用高级搜索还是简单搜索
        const searchEndpoint = useAdvancedSearch ? '/advanced_search' : '/simple_search';
        
        // 发送搜索请求
        fetch(searchEndpoint, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // 隐藏加载指示器
            loadingIndicator.classList.add('d-none');
            
            if (data.success) {
                resultStats.textContent = data.message;
                
                // 显示搜索结果
                if (data.items.length > 0) {
                    console.log("服务器返回的数据:", JSON.stringify(data.items[0]));
                    displaySearchResults(data.items);
                } else {
                    const emptyMessage = '<div class="col-12 empty-results"><i class="bi bi-search" style="font-size: 2rem;"></i><p class="mt-3">没有找到匹配的商品</p></div>';
                    searchResults.innerHTML = emptyMessage;
                    searchResultsTable.innerHTML = `<tr><td colspan="6" class="text-center py-5">${emptyMessage}</td></tr>`;
                }
            } else {
                // 显示错误信息
                errorMessage.textContent = data.message;
                errorMessage.classList.remove('d-none');
            }
        })
        .catch(error => {
            // 处理错误
            loadingIndicator.classList.add('d-none');
            errorMessage.textContent = '搜索请求失败：' + error.message;
            errorMessage.classList.remove('d-none');
        });
    });
    
    // 显示搜索结果
    function displaySearchResults(items) {
        searchResults.innerHTML = '';
        searchResultsTable.innerHTML = '';
        
        items.forEach(item => {
            console.log("处理商品:", item.title);
            console.log("价格信息:", item.price);
            console.log("发布时间:", item.postTime);
            console.log("位置信息:", item.location);
            console.log("图片信息:", item.image);
            
            // 卡片视图
            const itemNode = document.importNode(itemTemplate.content, true);
            
            // 填充数据
            itemNode.querySelector('.item-title').textContent = item.title;
            itemNode.querySelector('.item-price').textContent = item.price || "未知价格";
            
            // 填充额外信息（如果有）
            const locationElement = itemNode.querySelector('.item-location');
            if (item.location && item.location.trim() !== '') {
                locationElement.innerHTML = `<i class="bi bi-geo-alt"></i> ${item.location}`;
                locationElement.style.display = 'inline-block';
            } else {
                locationElement.style.display = 'none';
            }
            
            const postTimeElement = itemNode.querySelector('.item-post-time');
            if (item.postTime && item.postTime.trim() !== '') {
                postTimeElement.innerHTML = `<i class="bi bi-clock"></i> ${item.postTime}`;
                postTimeElement.style.display = 'inline-block';
            } else {
                postTimeElement.style.display = 'none';
            }
            
            const imgElement = itemNode.querySelector('.item-image');
            if (item.image && item.image.trim() !== '') {
                console.log('设置商品图片URL:', item.image); // 调试信息
                imgElement.src = item.image;
                imgElement.onerror = function() {
                    console.log('图片加载失败，使用占位图');
                    this.src = 'https://via.placeholder.com/200x200?text=无法加载图片';
                };
            } else {
                console.log('商品无图片');
                imgElement.src = 'https://via.placeholder.com/200x200?text=无图片';
            }
            
            // 设置收藏按钮属性
            const addButton = itemNode.querySelector('.add-collection');
            addButton.dataset.itemId = item.itemId;
            
            // 添加到结果区域
            searchResults.appendChild(itemNode);
            
            // 表格视图
            const tableRow = document.importNode(tableRowTemplate.content, true);
            
            // 填充表格数据
            tableRow.querySelector('.item-title').textContent = item.title;
            tableRow.querySelector('.item-price').textContent = item.price || "未知价格";
            tableRow.querySelector('.item-post-time').textContent = item.postTime || '未知';
            tableRow.querySelector('.item-location').textContent = item.location || '未知';
            
            const tableImgElement = tableRow.querySelector('.item-image');
            if (item.image && item.image.trim() !== '') {
                tableImgElement.src = item.image;
                tableImgElement.onerror = function() {
                    this.src = 'https://via.placeholder.com/90x90?text=无法加载';
                };
            } else {
                tableImgElement.src = 'https://via.placeholder.com/90x90?text=无图片';
            }
            
            // 设置收藏按钮属性
            const tableAddButton = tableRow.querySelector('.add-collection');
            tableAddButton.dataset.itemId = item.itemId;
            
            // 添加到表格结果区域
            searchResultsTable.appendChild(tableRow);
        });
        
        // 为所有收藏按钮添加事件监听
        document.querySelectorAll('.add-collection').forEach(button => {
            button.addEventListener('click', function() {
                const itemId = this.dataset.itemId;
                addToCollection(itemId, this);
            });
        });
    }
    
    // 加载地区列表
    function loadLocations() {
        fetch('/get_locations')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.locations) {
                    data.locations.forEach(location => {
                        const option = document.createElement('option');
                        option.value = location.code;
                        option.textContent = location.name;
                        locationSelect.appendChild(option);
                    });
                }
            })
            .catch(error => {
                console.error('加载地区列表失败:', error);
            });
    }
    
    // 添加到收藏
    function addToCollection(itemId, buttonElement) {
        // 禁用按钮，防止重复点击
        buttonElement.disabled = true;
        buttonElement.textContent = '添加中...';
        
        const formData = new FormData();
        formData.append('item_id', itemId);
        
        fetch('/add_collection', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                buttonElement.textContent = '已收藏';
                buttonElement.classList.remove('btn-primary');
                buttonElement.classList.add('btn-success');
            } else {
                buttonElement.textContent = '添加失败';
                buttonElement.classList.remove('btn-primary');
                buttonElement.classList.add('btn-danger');
                buttonElement.disabled = false;
                
                // 显示错误消息
                showToast(data.message, 'danger');
            }
        })
        .catch(error => {
            buttonElement.textContent = '添加失败';
            buttonElement.classList.remove('btn-primary');
            buttonElement.classList.add('btn-danger');
            buttonElement.disabled = false;
            
            // 显示错误消息
            showToast('添加收藏失败：' + error.message, 'danger');
        });
    }
    
    // 清空收藏列表
    clearCollectionsBtn.addEventListener('click', function() {
        if (!confirm('确定要清空收藏列表吗？此操作不可恢复。')) {
            return;
        }
        
        this.disabled = true;
        this.innerHTML = '<i class="bi bi-hourglass-split"></i> 正在清空...';
        
        fetch('/clear_collections', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            this.disabled = false;
            this.innerHTML = '<i class="bi bi-trash"></i> 清空收藏列表';
            
            if (data.success) {
                showToast(data.message, 'success');
            } else {
                showToast(data.message, 'danger');
            }
        })
        .catch(error => {
            this.disabled = false;
            this.innerHTML = '<i class="bi bi-trash"></i> 清空收藏列表';
            showToast('清空收藏列表失败：' + error.message, 'danger');
        });
    });
    
    // 显示通知
    function showToast(message, type) {
        // 检查是否已存在toast容器
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }
        
        // 创建新的toast
        const toastId = 'toast-' + Date.now();
        const toast = document.createElement('div');
        toast.className = `toast show bg-${type} text-white`;
        toast.id = toastId;
        toast.role = 'alert';
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="toast-header bg-${type} text-white">
                <strong class="me-auto">${type === 'success' ? '成功' : '错误'}</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        // 添加到容器
        toastContainer.appendChild(toast);
        
        // 3秒后自动关闭
        setTimeout(() => {
            toast.remove();
        }, 3000);
        
        // 为关闭按钮添加事件
        toast.querySelector('.btn-close').addEventListener('click', function() {
            toast.remove();
        });
    }
}); 