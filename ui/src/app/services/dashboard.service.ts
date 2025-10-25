import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';
import { SocketIoService } from './socket-io.service';

export interface DashboardStats {
  total_documents: number;
  status_counts: { [status: string]: number };
  category_counts: { name: string; value: number }[];
  docs_over_time: { name: string; value: number }[];
  pending_users: number;
}

@Injectable({
  providedIn: 'root'
})
export class DashboardService {
  private apiUrl = '/api/v1/dashboard/stats';

  private refreshNeeded$ = new Subject<void>();

  constructor(private http: HttpClient, private socketService: SocketIoService) {
    // In a real app, you would connect to a socket service here
    // this.socketService.listen('dashboard_update').subscribe(() => {
    //   this.refreshNeeded$.next();
    // });
  }

  getStats(): Observable<DashboardStats> {
    return this.http.get<DashboardStats>(this.apiUrl);
  }

  onRefreshNeeded(): Observable<void> {
    return this.refreshNeeded$.asObservable();
  }
}