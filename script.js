document.addEventListener('DOMContentLoaded', () => {
    // 1. Auth & State
    const token = localStorage.getItem('authToken');
    const userStr = localStorage.getItem('liftops_user');

    if (!token) {
        window.location.href = '/login.html';
        return;
    }

    const user = userStr ? JSON.parse(userStr) : {};
    let currentTier = localStorage.getItem('liftops_tier') || user.tier || 'pilot';

    // Auto-update Tier if Admin
    if (user.role === 'admin') {
        currentTier = 'commander';
        localStorage.setItem('liftops_tier', 'commander');
    }

    // 2. DOM Elements
    const navDashboard = document.getElementById('nav-dashboard');
    const navLogs = document.getElementById('nav-logs');
    const navSettings = document.getElementById('nav-settings');

    const dashboardGrid = document.querySelector('.pipeline-grid');
    const inputSection = document.querySelector('.input-section');
    const logsSection = document.getElementById('logs-section');
    const settingsSection = document.getElementById('settings-section');

    // Payment UI
    const paywallModal = document.getElementById('paywall-modal');
    const closePaywallBtn = document.getElementById('close-paywall');
    const submitPaymentBtn = document.getElementById('submit-payment-btn');
    const paymentMessage = document.getElementById('payment-message');
    let stripe;
    let elements;
    let isPaymentElementLoaded = false;

    // 3. Navigation
    function toggleView(viewName) {
        navDashboard.classList.remove('active');
        navLogs.classList.remove('active');
        if (navSettings) navSettings.classList.remove('active');

        dashboardGrid.style.display = 'none';
        inputSection.style.display = 'none';
        if (logsSection) logsSection.classList.add('hidden');
        if (settingsSection) settingsSection.classList.add('hidden');

        if (viewName === 'dashboard') {
            navDashboard.classList.add('active');
            dashboardGrid.style.display = 'grid';
            inputSection.style.display = 'flex';
        } else if (viewName === 'logs') {
            navLogs.classList.add('active');
            if (logsSection) {
                logsSection.classList.remove('hidden');
                loadLogs();
            }
        } else if (viewName === 'settings') {
            if (navSettings) navSettings.classList.add('active');
            if (settingsSection) settingsSection.classList.remove('hidden');
        }
    }

    navDashboard.addEventListener('click', (e) => { e.preventDefault(); toggleView('dashboard'); });
    navLogs.addEventListener('click', (e) => { e.preventDefault(); toggleView('logs'); });

    if (navSettings) {
        navSettings.addEventListener('click', (e) => {
            e.preventDefault();
            // Check Tier
            if (currentTier === 'commander') {
                toggleView('settings');
            } else {
                if (paywallModal) {
                    paywallModal.classList.remove('hidden');
                    loadPaymentForm();
                }
            }
        });
    }

    if (closePaywallBtn) {
        closePaywallBtn.addEventListener('click', () => {
            paywallModal.classList.add('hidden');
        });
    }

    // 4. Payment Logic (Stripe)

    // Initialize Stripe
    async function initStripe() {
        try {
            const res = await fetch('/api/config/stripe-key');
            const { publishableKey } = await res.json();
            stripe = Stripe(publishableKey);
        } catch (err) {
            console.error('Failed to load Stripe key', err);
        }
    }
    initStripe();

    async function loadPaymentForm() {
        if (isPaymentElementLoaded) return;

        try {
            const res = await fetch('/api/create-payment-intent', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: user.email || 'guest@example.com' }) // Fallback for guest
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || `Server Error: ${res.status}`);
            }

            const { clientSecret } = await res.json();

            const appearance = { theme: 'night', labels: 'floating' };
            elements = stripe.elements({ appearance, clientSecret });

            const paymentElement = elements.create('payment');
            paymentElement.mount('#payment-element');
            isPaymentElementLoaded = true;
        } catch (e) {
            console.error("Error loading payment form", e);
            if (paymentMessage) {
                paymentMessage.textContent = "Failed to load payment form. Check server logs.";
                paymentMessage.classList.remove('hidden');
            }
        }
    }

    if (submitPaymentBtn) {
        submitPaymentBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            if (!stripe || !elements) return;

            setLoading(true);

            const { error, paymentIntent } = await stripe.confirmPayment({
                elements,
                confirmParams: {
                    // Make sure to change this to your payment completion page
                    return_url: window.location.href, // For redirects, but we use redirect: if_required
                },
                redirect: 'if_required'
            });

            if (error) {
                showMessage(error.message);
                setLoading(false);
            } else if (paymentIntent && paymentIntent.status === 'succeeded') {
                // Verify with backend and upgrade
                await verifyAndUpgrade(paymentIntent.id);
            } else {
                showMessage("Unexpected payment status.");
                setLoading(false);
            }
        });
    }

    async function verifyAndUpgrade(paymentIntentId) {
        try {
            const res = await fetch('/api/verify-payment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    paymentIntentId,
                    email: user.email || 'guest@example.com'
                })
            });

            const data = await res.json();
            if (res.ok && data.status === 'success') {
                showMessage("Payment Success! Upgrading...", false);
                // Update State
                currentTier = 'commander';
                localStorage.setItem('liftops_tier', 'commander');

                setTimeout(() => {
                    if (paywallModal) paywallModal.classList.add('hidden');
                    toggleView('settings');
                    setLoading(false);
                }, 1500);
            } else {
                throw new Error(data.details || "Upgrade failed");
            }
        } catch (err) {
            showMessage("Payment succeeded but upgrade failed: " + err.message);
            setLoading(false);
        }
    }

    function showMessage(messageText, isError = true) {
        if (!paymentMessage) return;
        paymentMessage.classList.remove('hidden');
        paymentMessage.textContent = messageText;
        paymentMessage.style.color = isError ? '#ff4444' : '#10b981';
    }

    function setLoading(isLoading) {
        if (isLoading) {
            submitPaymentBtn.disabled = true;
            document.querySelector('#spinner').classList.remove('hidden');
            document.querySelector('#button-text').classList.add('hidden');
        } else {
            submitPaymentBtn.disabled = false;
            document.querySelector('#spinner').classList.add('hidden');
            document.querySelector('#button-text').classList.remove('hidden');
        }
    }

    // 5. Dashboard Pipeline Logic (Standard)
    const inputField = document.getElementById('user-input');
    const submitBtn = document.getElementById('submit-btn');
    const panels = {
        router: { card: document.getElementById('card-router'), output: document.getElementById('router-output') },
        planner: { card: document.getElementById('card-planner'), output: document.getElementById('planner-output') },
        executor: { card: document.getElementById('card-executor'), output: document.getElementById('executor-output') },
        validator: { card: document.getElementById('card-validator'), output: document.getElementById('validator-output') }
    };

    if (submitBtn) {
        submitBtn.addEventListener('click', () => {
            const userInput = inputField.value.trim();
            if (!userInput) return;
            runPipeline(userInput);
        });
    }

    async function runPipeline(input) {
        Object.values(panels).forEach(p => {
            p.output.textContent = '// Waiting...';
            p.card.classList.remove('processing');
            p.card.querySelector('.status-badge').textContent = 'Idle';
        });

        inputField.disabled = true;
        submitBtn.disabled = true;
        submitBtn.querySelector('.btn-text').textContent = 'Running...';

        try {
            // Processing logic...
            const response = await fetch('/api/antigravity/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ input: input })
            });
            const data = await response.json();

            // ... Visuals ...
            await updatePanel('router', data.router);
            await updatePanel('planner', data.planner);
            await updatePanel('executor', data.executor);
            await updatePanel('validator', data.validator);

        } catch (error) {
            console.error(error);
        } finally {
            inputField.disabled = false;
            submitBtn.disabled = false;
            submitBtn.querySelector('.btn-text').textContent = 'Execute Pipeline';
        }
    }

    function setProcessing(stage, isActive) {
        if (!panels[stage]) return;
        const panel = panels[stage];
        if (isActive) {
            panel.card.classList.add('processing');
            panel.card.querySelector('.status-badge').textContent = 'Processing';
        } else {
            panel.card.classList.remove('processing');
            panel.card.querySelector('.status-badge').textContent = 'Complete';
        }
    }

    function updatePanel(stage, data) {
        return new Promise(resolve => {
            setProcessing(stage, true);
            setTimeout(() => {
                panels[stage].output.textContent = JSON.stringify(data, null, 2);
                setProcessing(stage, false);
                resolve();
            }, 600);
        });
    }

    // 6. Logs Logic (Mock)
    const refreshBtn = document.getElementById('refresh-logs');
    if (refreshBtn) refreshBtn.addEventListener('click', loadLogs);

    async function loadLogs() {
        // ... (Same log logic as before) ...
        const logsBody = document.getElementById('logs-body');
        logsBody.innerHTML = '<tr><td colspan="5">Loading...</td></tr>';
        const res = await fetch('/api/antigravity/history');
        const history = await res.json();
        // ... render ...
        renderLogs(history);
    }

    function renderLogs(history) {
        const logsBody = document.getElementById('logs-body');
        logsBody.innerHTML = '';
        history.forEach(entry => {
            const tr = document.createElement('tr');
            const isValid = entry.validator?.valid ?? false;
            const safetyClass = isValid ? 'badge-safe' : 'badge-unsafe';
            const safetyText = isValid ? 'Valid' : 'Blocked';
            const statusDot = isValid ? '<span class="dot online"></span>' : '<span class="dot error"></span>';

            tr.innerHTML = `
                    <td>${statusDot}</td>
                    <td>${new Date(entry.saved_at || Date.now()).toLocaleTimeString()}</td>
                    <td class="mono">${entry.request_id ? entry.request_id.slice(0, 8) : 'N/A'}...</td>
                    <td>${entry.router?.intent || 'Unknown'}</td>
                    <td><span class="badge ${safetyClass}">${safetyText}</span></td>
                `;
            logsBody.appendChild(tr);
        });
    }
});
