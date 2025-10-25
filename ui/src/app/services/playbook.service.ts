import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

// Define the models for Playbook and PlaybookStep
// These should match the Pydantic models on the backend.
export interface PlaybookStep {
  type: string;
  name: string;
  [key: string]: any; // Allow other properties
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

  private apiUrl = '/api'; // Assuming the Flask API is proxied under /api

  constructor(private http: HttpClient) { }

  // --- Playbook Methods ---

  getPlaybooks(category_name?: string): Observable<Playbook[]> {
    let url = `${this.apiUrl}/playbooks`;
    if (category_name) {
      url += `?category_name=${category_name}`;
    }
    return this.http.get<Playbook[]>(url);
  }

  getPlaybook(id: string): Observable<Playbook> {
    return this.http.get<Playbook>(`${this.apiUrl}/playbooks/${id}`);
  }

  createPlaybook(playbook: Playbook): Observable<Playbook> {
    return this.http.post<Playbook>(`${this.apiUrl}/playbooks`, playbook);
  }

  updatePlaybook(id: string, playbook: Playbook): Observable<Playbook> {
    return this.http.put<Playbook>(`${this.apiUrl}/playbooks/${id}`, playbook);
  }

  deletePlaybook(id: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/playbooks/${id}`);
  }

  // --- Step Metadata Method ---

  getStepMetadata(): Observable<any> {
    return this.http.get(`${this.apiUrl}/playbooks/steps`);
  }
}
