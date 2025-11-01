
import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

// Define the Playbook model based on your backend
export interface PlaybookStep {
  type: string;
  name: string;
  on_failure?: any;
  [key: string]: any; // Allow other dynamic properties
}

export interface Playbook {
  _id?: string;
  name: string;
  category_name: string;
  steps: PlaybookStep[];
  final_status?: string;
  created_at?: string;
}

@Injectable({
  providedIn: 'root'
})
export class PlaybookService {
  private apiUrl = '/api/v1/playbooks';

  constructor(private http: HttpClient) { }

  // Create a new playbook
  createPlaybook(playbook: Playbook): Observable<Playbook> {
    return this.http.post<Playbook>(this.apiUrl, playbook);
  }

  // Get all playbooks, optionally filtered by category
  getPlaybooks(categoryName?: string): Observable<Playbook[]> {
    let params = new HttpParams();
    if (categoryName) {
      params = params.set('category_name', categoryName);
    }
    return this.http.get<Playbook[]>(this.apiUrl, { params });
  }

  // Get a single playbook by its ID
  getPlaybook(id: string): Observable<Playbook> {
    return this.http.get<Playbook>(`${this.apiUrl}/${id}`);
  }

  // Update a playbook
  updatePlaybook(id: string, playbook: Playbook): Observable<Playbook> {
    return this.http.put<Playbook>(`${this.apiUrl}/${id}`, playbook);
  }

  // Delete a playbook
  deletePlaybook(id: string): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.apiUrl}/${id}`);
  }
}
