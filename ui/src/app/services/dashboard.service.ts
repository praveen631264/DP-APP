import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';
import { SocketIoService } from './socket-io.service';
import { environment } from '../../environments/environment';

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
  private apiUrl = `${environment.apiUrl}/dashboard/stats`;

  private refreshNeeded$ = new Subject<void>();

  constructor(private http: HttpClient, private socketService: SocketIoService) {
    this.socketService.listen('dashboard_update').subscribe(() => {
      this.refreshNeeded$.next();
    });
  }

  getStats(): Observable<DashboardStats> {
    return this.http.get<DashboardStats>(this.apiUrl);
  }

  onRefreshNeeded(): Observable<void> {
    return this.refreshNeeded$.asObservable();
  }
}
