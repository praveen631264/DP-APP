
import { Routes } from '@angular/router';
import { DocumentListComponent } from './document-list/document-list.component';
import { DocumentDetailComponent } from './document-detail/document-detail.component';
import { DocumentEditComponent } from './document-edit/document-edit.component';
import { DashboardComponent } from './dashboard/dashboard.component';
import { LayoutComponent } from './layout/layout.component';

export const routes: Routes = [
    {
        path: '',
        component: LayoutComponent,
        children: [
            { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
            { path: 'dashboard', component: DashboardComponent },
            { path: 'documents', component: DocumentListComponent },
            { path: 'documents/:id', component: DocumentDetailComponent },
            { path: 'documents/:id/edit', component: DocumentEditComponent }
        ]
    }
];
