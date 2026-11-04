//Starter catalog, only added when the shop has no products yet
const starterProducts = [
    { id: 1, name: 'Kirby Plush', price: 24.99 },
    { id: 2, name: 'Warp Star Lamp', price: 39.5 },
    { id: 3, name: 'Maxim Tomato Snack', price: 4.99 },
    { id: 4, name: 'Star Rod Replica', price: 54 },
    { id: 5, name: 'Kirby Keychain', price: 8.75 },
    { id: 6, name: 'Kirby Sleepy Cap', price: 18 }
];

// Open (or create) the database with the version 2
let db;
const request = indexedDB.open('exampleProductDB', 2);

request.onerror = function(event) {
    console.error("Database error: ", event.target.error);
};

request.onsuccess = function(event) {
    db = event.target.result;
    loadProducts(); // Load products after the database is opened
};

request.onupgradeneeded = function(event) {
    db = event.target.result;
    const store = event.oldVersion < 1
        ? db.createObjectStore('products', { keyPath: 'id' })
        : event.target.transaction.objectStore('products');

    //Fill the shop with the starter catalog if it is empty
    const countRequest = store.count();
    countRequest.onsuccess = function() {
        if (countRequest.result === 0) {
            starterProducts.forEach(product => store.add(product));
        }
    };
};

//Choose the illustration of a product based on its name
function getProductArt(name) {
    const lowerName = name.toLowerCase();
    if (lowerName.includes('star')) return '#art-star';
    if (lowerName.includes('tomato')) return '#art-tomato';
    return '#art-kirby';
}

//Create the card of a product
function createProductCard(product) {
    const card = document.createElement('article');
    card.className = 'productCard';
    card.innerHTML = `
        <div class="productArt">
            <svg aria-hidden="true"><use href="${getProductArt(product.name)}"/></svg>
        </div>
        <div class="productInfo">
            <span class="productId"></span>
            <h3 class="productName"></h3>
            <div class="productFooter">
                <span class="productPrice"></span>
                <button class="delete-btn" data-id="${product.id}">Delete</button>
            </div>
        </div>
    `;
    //Use textContent so the product name is never read as HTML
    card.querySelector('.productId').textContent = 'No. ' + product.id;
    card.querySelector('.productName').textContent = product.name;
    card.querySelector('.productPrice').textContent = '$' + product.price.toFixed(2);
    card.querySelector('.delete-btn').setAttribute('aria-label', 'Delete ' + product.name);
    return card;
}

//Load/Read products from IndexedDB and display them in the catalog
function loadProducts() {
    const transaction = db.transaction(['products'], 'readonly');
    const store = transaction.objectStore('products');

    const request = store.getAll();

    request.onsuccess = function(event) {
        const products = event.target.result;
        const grid = document.getElementById('productsGrid');
        grid.innerHTML = ''; // Clear the catalog before adding the products

        products.forEach(product => {
            grid.appendChild(createProductCard(product));
        });

    //Show the empty message when there are no products
        document.getElementById('emptyShop').hidden = products.length > 0;

    //Update the inventory summary
        updateSummary(products);

    //Add event listeners for delete buttons
        document.querySelectorAll('.delete-btn').forEach(button => {
            button.addEventListener('click', deleteProduct);
        });
    };
}

//Show the number of products and the total value of the inventory
function updateSummary(products) {
    const total = products.reduce((sum, product) => sum + product.price, 0);
    document.getElementById('totalProducts').textContent = products.length;
    document.getElementById('totalValue').textContent = '$' + total.toFixed(2);
}

//Add/Create a new product
function addProduct() {
    const name = document.getElementById('name').value.trim();
    const price = parseFloat(document.getElementById('price').value);

    //Validate inputs
    if (!name || isNaN(price) || price <= 0) {
        alert("Please enter a valid name and price.");
        return;
    }

    const transaction = db.transaction(['products'], 'readwrite');
    const store = transaction.objectStore('products');

    //Get/Read the products
    const getAllRequest = store.getAll();

    getAllRequest.onsuccess = function(event) {
        const products = event.target.result;
        const newProduct = {
            id: products.length > 0 ? products[products.length - 1].id + 1 : 1, // Assign an incremental ID
            name: name,
            price: price
        };

    //Add/Create the new product to the DB
        store.add(newProduct);
        //Clear the form fields
        document.getElementById('name').value = '';
        document.getElementById('price').value = '';

    //Update the catalog with the new product
        loadProducts();
    };
}

//Delete a product
function deleteProduct(event) {
    const productId = parseInt(event.target.getAttribute('data-id')); // Get the product ID from the button's data attribute
    const transaction = db.transaction(['products'], 'readwrite');
    const store = transaction.objectStore('products');

    //Delete the product with the corresponding ID
    store.delete(productId);

    //Reload the catalog to reflect changes
    loadProducts();
}

//Event listener for the button click
document.getElementById('addProduct').addEventListener('click', addProduct);
