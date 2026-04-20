import { createRouter, createWebHistory } from 'vue-router';

import NewsletterIndex from './modules/newsletter/NewsletterIndex.vue';
import CampaignEditor  from './modules/newsletter/CampaignEditor.vue';
import PromoIndex      from './modules/promo/PromoIndex.vue';
import Dashboard       from './modules/Dashboard.vue';

export const router = createRouter({
  history: createWebHistory('/admin'),
  routes: [
    { path: '/',                    component: Dashboard },
    { path: '/newsletter',          component: NewsletterIndex },
    { path: '/newsletter/:id',      component: CampaignEditor },
    { path: '/promo',               component: PromoIndex },
  ],
});
