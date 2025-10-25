import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface DashboardStats {
  total_documents: number;
  status_counts: { [key: string]: number };
  category_counts: { name: string; value: number }[];
  docs_over_time: { name: string; value: number }[];
  pending_users: number;
}

@Injectable({
  providedIn: 'root'
})
export class DashboardService {

  private apiUrl = '/api/dashboard';

  constructor(private http: HttpClient) { }

  getStats(): Observable<DashboardStats> {
    return this.http.get<DashboardStats>(`${this.apiUrl}/stats`);
  }
}
