import { Routes } from '@angular/router';
import { LayoutComponent } from './layout/layout.component';
import { adminGuard } from './auth.guard';
import { LoginComponent } from './login/login.component';
import { loginGuard } from './login.guard';
import { SettingsComponent } from './settings/settings.component';
import { UserManagementComponent } from './user-management/user-management.component';
import { AuditLogComponent } from './audit-log/audit-log.component';
import { CategoryManagementComponent } from './category-management/category-management.component';
import { PlaybookListComponent } from './playbook-list/playbook-list.component';
import { PlaybookEditorComponent } from './playbook-editor/playbook-editor.component';

export const routes: Routes = [
  { path: 'login', component: LoginComponent, canActivate: [loginGuard] },
  {
    path: '',
    component: LayoutComponent,
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      {
        path: 'dashboard',
        loadComponent: () => import('./dashboard/dashboard.component').then(m => m.DashboardComponent)
      },
      {
        path: 'documents',
        loadComponent: () => import('./document-list/document-list.component').then(m => m.DocumentListComponent)
      },
      {
        path: 'document-viewer/:id',
        loadComponent: () => import('./document-viewer/document-viewer.component').then(m => m.DocumentViewerComponent)
      },
      {
        path: 'playbooks',
        component: PlaybookListComponent
      },
      {
        path: 'playbooks/new',
        component: PlaybookEditorComponent
      },
      {
        path: 'playbooks/:id/edit',
        component: PlaybookEditorComponent
      },
      {
        path: 'category-management',
        component: CategoryManagementComponent,
        canActivate: [adminGuard]
      },
      {
        path: 'user-management',
        component: UserManagementComponent,
        canActivate: [adminGuard]
      },
      {
        path: 'audit-log',
        component: AuditLogComponent,
        canActivate: [adminGuard]
      },
      {
        path: 'settings',
        component: SettingsComponent
      },
      {
        path: 'global-search',
        loadComponent: () => import('./global-search/global-search.component').then(m => m.GlobalSearchComponent)
      },
      { 
        path: 'workflow-monitoring/:id', 
        loadComponent: () => import('./workflow-viewer/workflow-viewer.component').then(m => m.WorkflowViewerComponent) 
      },
      { path: 'workflow-monitoring', loadComponent: () => import('./document-list/document-list.component').then(m => m.DocumentListComponent) }
    ],
  },
];