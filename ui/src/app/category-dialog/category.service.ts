import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { delay } from 'rxjs/operators';

export interface PromptSuggestion {
  prompt: string;
}

@Injectable({
  providedIn: 'root'
})
export class CategoryService {
  constructor(private http: HttpClient) { }

  getPromptSuggestion(description: string): Observable<PromptSuggestion> {
    // In a real app: return this.http.post<PromptSuggestion>('/api/v1/categories/suggest-prompt', { description });
    return of({ prompt: `Based on "${description}", extract key details like invoice number, date, and total.` }).pipe(delay(1000));
  }
}