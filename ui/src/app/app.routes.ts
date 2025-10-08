import { Routes } from '@angular/router';
import { DashboardComponent } from './dashboard/dashboard';
import { ChatComponent } from './chat/chat';

export const routes: Routes = [
    { path: '', component: DashboardComponent },
    { path: 'chat', component: ChatComponent }
];
