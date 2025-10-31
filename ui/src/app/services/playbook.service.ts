import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';
import { SocketIoService } from './socket-io.service';
import { environment } from '../../environments/environment';

export interface PlaybookStep {
  type: string;
  name: string;
  [key: string]: any;
}

export interface Playbook {
  _id?: string;
  name: string;
  category_name: string;
  steps: PlaybookStep[];
  final_status?: string;
}

@Injectable({
  providedIn: 'root'
})
export class PlaybookService {
  private apiUrl = `${environment.apiUrl}/v1/playbooks`;
  private refreshNeeded$ = new Subject<void>();

  constructor(private http: HttpClient, private socketService: SocketIoService) {
    this.socketService.listen('playbook_updated').subscribe(() => {
      this.refreshNeeded$.next();
    });

    this.socketService.listen('playbook_deleted').subscribe(() => {
      this.refreshNeeded$.next();
    });
  }

  getPlaybooks(category_name?: string): Observable<Playbook[]> {
    let url = this.apiUrl;
    if (category_name) {
      url += `?category_name=${category_name}`;
    }
    return this.http.get<Playbook[]>(url);
  }

  getPlaybook(id: string): Observable<Playbook> {
    return this.http.get<Playbook>(`${this.apiUrl}/${id}`);
  }

  createPlaybook(playbook: Playbook): Observable<any> {
    return this.http.post(this.apiUrl, playbook);
  }

  updatePlaybook(id: string, playbook: Playbook): Observable<any> {
    return this.http.put(`${this.apiUrl}/${id}`, playbook);
  }

  deletePlaybook(id: string): void {
    this.socketService.emit('delete_playbook', { id });
  }

  getStepMetadata(): Observable<any> {
    return this.http.get(`${this.apiUrl}/steps`);
  }

  onRefreshNeeded(): Observable<void> {
    return this.refreshNeeded$.asObservable();
  }
}
