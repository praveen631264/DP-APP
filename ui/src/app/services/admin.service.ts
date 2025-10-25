import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface User {
  id: string;
  email: string;
  mfa_enabled: boolean;
  active: boolean;
  approved: boolean;
  roles: string[];
  confirmed_at: string;
  created_at: string;
}

export interface Policy {
  resource: string;
  policy: { [key: string]: any };
  description: string;
}

export interface AuditLog {
  items: any[];
  total: number;
}

@Injectable({
  providedIn: 'root'
})
export class AdminService {
  private apiUrl = '/api/v1/admin';

  constructor(private http: HttpClient) { }

  getUsers(): Observable<User[]> {
    return this.http.get<User[]>(`${this.apiUrl}/users`);
  }

  updateUser(userId: string, payload: { approved?: boolean; roles?: string[] }): Observable<any> {
    return this.http.put(`${this.apiUrl}/users/${userId}`, payload);
  }

  getPolicies(): Observable<Policy[]> {
    return this.http.get<Policy[]>(`${this.apiUrl}/policies`);
  }

  createPolicy(policy: Policy): Observable<any> {
    return this.http.post(`${this.apiUrl}/policies`, policy);
  }

  deletePolicy(resource: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/policies/${encodeURIComponent(resource)}`);
  }

  getRoles(): Observable<string[]> {
    return this.http.get<string[]>(`${this.apiUrl}/roles`);
  }

  getAuditLog(page: number, limit: number, filters: any): Observable<AuditLog> {
    let params: any = { page, limit };
    if (filters.action) params.action = filters.action;
    if (filters.user_email) params.user_email = filters.user_email;

    return this.http.get<AuditLog>(`${this.apiUrl}/audit-log`, { params });
  }

  resetMfa(userId: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/users/${userId}/reset-mfa`, {});
  }
}