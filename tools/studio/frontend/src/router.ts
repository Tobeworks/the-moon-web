import { createRouter, createWebHashHistory } from 'vue-router';
import NewReleaseView from '@/views/NewReleaseView.vue';
import OverviewView from '@/views/OverviewView.vue';
import ReleaseView from '@/views/ReleaseView.vue';

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: OverviewView },
    { path: '/new', component: NewReleaseView },
    { path: '/r/:catalog(TMR-\\d+)/:focus?', component: ReleaseView, props: true },
    { path: '/:rest(.*)*', redirect: '/' },
  ],
});
