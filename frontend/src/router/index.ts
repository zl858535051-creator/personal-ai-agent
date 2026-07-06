import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/ChatView.vue'
import UploadView from '../views/UploadView.vue'
import HistoryView from '../views/HistoryView.vue'
import ReportView from '../views/ReportView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: ChatView },
    { path: '/upload', component: UploadView },
    { path: '/history', component: HistoryView },
    { path: '/reports', component: ReportView }
  ]
})

