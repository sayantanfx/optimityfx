/* ============================================================
   OptimityFX — Auth & Session Utilities
   Depends on: Supabase CDN (global: window.supabase), config.js
   Include on every page before main.js
   ============================================================ */
(function () {
  'use strict';

  if (!window.supabase) { console.warn('OFXAuth: Supabase CDN not loaded'); return; }
  if (!window.OFX)     { console.warn('OFXAuth: config.js not loaded'); return; }

  const isConfigured = !OFX.supabaseUrl.startsWith('YOUR_');

  const { createClient } = window.supabase;
  let sb = null;
  if (isConfigured) {
    try { sb = createClient(OFX.supabaseUrl, OFX.supabaseKey); }
    catch (e) { console.error('OFXAuth: createClient failed —', e.message); }
  } else {
    console.warn('OFXAuth: Supabase not configured yet — fill in js/config.js. URL starts with YOUR_');
  }

  /* ================================================================
     CART (localStorage)
  ================================================================ */
  const Cart = {
    get()         { try { return JSON.parse(localStorage.getItem('ofx_cart') || '[]'); } catch { return []; } },
    save(c)       { localStorage.setItem('ofx_cart', JSON.stringify(c)); Cart.updateBadge(); },
    add(product)  { const c = Cart.get(); if (!c.find(p => p.id === product.id)) c.push(product); Cart.save(c); Cart.flashBadge(); },
    remove(id)    { Cart.save(Cart.get().filter(p => p.id !== id)); },
    clear()       { localStorage.removeItem('ofx_cart'); Cart.updateBadge(); },
    count()       { return Cart.get().length; },
    total()       { return Cart.get().reduce((s, p) => s + (p.sale_price || p.price || 0), 0); },
    updateBadge() {
      document.querySelectorAll('.cart-badge').forEach(el => {
        const n = Cart.count();
        el.textContent = n;
        el.style.display = n > 0 ? '' : 'none';
      });
    },
    flashBadge() {
      Cart.updateBadge();
      document.querySelectorAll('.cart-badge').forEach(el => {
        el.classList.add('pop');
        setTimeout(() => el.classList.remove('pop'), 500);
      });
    },
  };

  /* ================================================================
     TOAST notifications
  ================================================================ */
  function toast(msg, type = 'info', dur = 3500) {
    let wrap = document.querySelector('.toast-wrap');
    if (!wrap) {
      wrap = document.createElement('div');
      wrap.className = 'toast-wrap';
      document.body.appendChild(wrap);
    }
    const t = document.createElement('div');
    t.className = `toast toast--${type}`;
    const icons = {
      success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M20 6 9 17l-5-5"/></svg>',
      error:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M18 6 6 18M6 6l12 12"/></svg>',
      info:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>',
      reward:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
    };
    t.innerHTML = `<span class="toast-icon">${icons[type] || icons.info}</span><span>${msg}</span><button class="toast-close" onclick="this.parentElement.remove()">×</button>`;
    wrap.appendChild(t);
    requestAnimationFrame(() => t.classList.add('show'));
    if (dur > 0) setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 350); }, dur);
  }

  /* ================================================================
     DAILY REWARDS
  ================================================================ */
  async function grantDailyReward(userId) {
    const today = new Date().toISOString().split('T')[0];
    const { data: existing } = await sb.from('login_rewards').select('id').eq('user_id', userId).eq('date', today).maybeSingle();
    if (existing) return;

    const { data: profile } = await sb.from('profiles').select('login_streak, last_login_date, wallet_credits, total_logins').eq('id', userId).maybeSingle();
    if (!profile) return;

    const yesterday = new Date(); yesterday.setDate(yesterday.getDate() - 1);
    const yStr = yesterday.toISOString().split('T')[0];
    let newStreak = (profile.last_login_date === yStr) ? (profile.login_streak || 0) + 1 : 1;
    if (newStreak > 7) newStreak = 1;

    const bonus = OFX.rewards.streakBonus[Math.min(newStreak - 1, 6)] || 0;
    const totalCredits = OFX.rewards.daily + bonus;

    await sb.from('login_rewards').insert({ user_id: userId, date: today, credits_earned: totalCredits, streak_day: newStreak });
    await sb.from('profiles').update({
      login_streak: newStreak, last_login_date: today,
      wallet_credits: (profile.wallet_credits || 0) + totalCredits,
      total_logins:   (profile.total_logins   || 0) + 1,
    }).eq('id', userId);
    await sb.from('wallet_transactions').insert({
      user_id: userId, type: 'earned', amount: totalCredits,
      description: `Daily login reward — Day ${newStreak} streak${bonus ? ` (+${bonus} streak bonus)` : ''}`,
    });

    setTimeout(() => {
      toast(`🎯 +${totalCredits} Credits! Day ${newStreak} streak${bonus ? ` (+${bonus} bonus)` : ''}`, 'reward', 5000);
    }, 1200);
  }

  /* ================================================================
     NAV UPDATE
  ================================================================ */
  async function updateNav() {
    let session = null;
    if (sb) { try { const r = await sb.auth.getSession(); session = r.data?.session; } catch {} }
    const navCta = document.querySelector('.nav-cta');
    const mDrawer = document.querySelector('.m-drawer');

    // Remove any existing auth btn
    document.querySelectorAll('.nav-auth-btn, .mobile-auth-link').forEach(el => el.remove());

    if (navCta) {
      const btn = document.createElement('a');
      btn.className = 'btn btn-ghost btn-sm nav-auth-btn';
      if (session) {
        btn.href = 'dashboard.html';
        btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" style="width:15px;height:15px"><circle cx="12" cy="8" r="4"/><path d="M4 20a8 8 0 0 1 16 0"/></svg> Dashboard`;
      } else {
        btn.href = 'login.html';
        btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" style="width:15px;height:15px"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3"/></svg> Sign In`;
      }
      navCta.insertBefore(btn, navCta.firstChild);
    }

    if (mDrawer) {
      const mLink = document.createElement('a');
      mLink.className = 'mobile-auth-link';
      if (session) { mLink.href = 'dashboard.html'; mLink.textContent = 'My Dashboard'; }
      else          { mLink.href = 'login.html';     mLink.textContent = 'Sign In';      }
      mDrawer.insertBefore(mLink, mDrawer.firstChild);
    }

    // Cart icon in nav
    const cartIcon = document.querySelector('.nav-cart');
    if (cartIcon) Cart.updateBadge();
  }

  /* ================================================================
     AUTH STATE LISTENER
  ================================================================ */
  if (sb) {
    sb.auth.onAuthStateChange(async (event, session) => {
      if (event === 'SIGNED_IN' && session) {
        await grantDailyReward(session.user.id);
      }
    });
  }

  /* ================================================================
     INIT
  ================================================================ */
  document.addEventListener('DOMContentLoaded', () => {
    updateNav();
    Cart.updateBadge();
  });

  /* ================================================================
     PUBLIC API  —  window.OFXAuth
  ================================================================ */
  window.OFXAuth = {
    sb, Cart, toast,

    async getSession() {
      if (!sb) return null;
      const { data: { session } } = await sb.auth.getSession();
      return session;
    },

    async getProfile(userId) {
      if (!sb) return null;
      try {
        const { data } = await sb.from('profiles').select('*').eq('id', userId).maybeSingle();
        return data;
      } catch { return null; }
    },

    async requireAuth(redirectTo) {
      if (!sb) return null; // unconfigured — don't block pages during dev
      const { data: { session } } = await sb.auth.getSession();
      if (!session) {
        const next = redirectTo || window.location.pathname + window.location.search;
        window.location.href = `login.html?next=${encodeURIComponent(next)}`;
        return null;
      }
      return session;
    },

    async signIn(email, password) {
      if (!sb) return { error: { message: 'Supabase not configured. Fill in js/config.js.' } };
      return sb.auth.signInWithPassword({ email, password });
    },

    async signUp(email, password, fullName) {
      if (!sb) return { data: null, error: { message: 'Supabase not configured. Fill in js/config.js.' } };
      const { data, error } = await sb.auth.signUp({
        email, password,
        options: { data: { full_name: fullName } },
      });
      if (!error && data.user) {
        await sb.from('profiles').upsert({
          id: data.user.id, email, full_name: fullName,
          role: 'customer', wallet_credits: 0, login_streak: 0,
        });
      }
      return { data, error };
    },

    async signInWithGoogle() {
      if (!sb) return;
      return sb.auth.signInWithOAuth({
        provider: 'google',
        options: { redirectTo: OFX.siteUrl + '/dashboard.html' },
      });
    },

    async signOut() {
      if (sb) await sb.auth.signOut();
      Cart.clear();
      window.location.href = 'index.html';
    },

    async resetPassword(email) {
      if (!sb) return { error: { message: 'Supabase not configured.' } };
      return sb.auth.resetPasswordForEmail(email, {
        redirectTo: OFX.siteUrl + '/reset-password.html',
      });
    },

    async updatePassword(newPassword) {
      if (!sb) return { error: { message: 'Supabase not configured.' } };
      return sb.auth.updateUser({ password: newPassword });
    },

    async validateCoupon(code, orderTotal) {
      if (!sb) return { valid: false, message: 'Coupons unavailable — Supabase not configured.' };
      const { data, error } = await sb
        .from('coupons')
        .select('*')
        .eq('code', code.toUpperCase().trim())
        .eq('is_active', true)
        .maybeSingle();
      if (error || !data) return { valid: false, message: 'Invalid coupon code.' };
      if (data.expires_at && new Date(data.expires_at) < new Date()) return { valid: false, message: 'Coupon has expired.' };
      if (data.max_uses && data.used_count >= data.max_uses) return { valid: false, message: 'Coupon usage limit reached.' };
      if (orderTotal < (data.min_order || 0)) return { valid: false, message: `Minimum order ₹${data.min_order} required.` };
      const discount = data.discount_type === 'percent'
        ? (orderTotal * data.discount_value / 100)
        : data.discount_value;
      return { valid: true, coupon: data, discount: Math.min(discount, orderTotal), message: `Coupon applied! You save ₹${Math.floor(discount)}.` };
    },

    updateNav,
  };
})();
