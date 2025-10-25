import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface CategoryPlaybook {
  name: string;
  description?: string;
  extraction_prompt?: string;
  workflow_steps?: any[];
}

export interface PromptSuggestion {
  generated_prompt: string;
}

@Injectable({
  providedIn: 'root'
})
export class CategoryService {
  private apiUrl = '/api/v1/categories';

  constructor(private http: HttpClient) { }

  getCategories(): Observable<CategoryPlaybook[]> {
    return this.http.get<CategoryPlaybook[]>(this.apiUrl);
  }

  createCategory(category: CategoryPlaybook): Observable<CategoryPlaybook> {
    return this.http.post<CategoryPlaybook>(this.apiUrl, category);
  }

  updateCategory(category: CategoryPlaybook): Observable<CategoryPlaybook> {
    return this.http.put<CategoryPlaybook>(`${this.apiUrl}/${encodeURIComponent(category.name)}`, category);
  }

  deleteCategory(categoryName: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${encodeURIComponent(categoryName)}`);
  }

  generateExtractionPrompt(categoryName: string, sampleText: string): Observable<PromptSuggestion> {
    return this.http.post<PromptSuggestion>(`${this.apiUrl}/${encodeURIComponent(categoryName)}/suggest-prompt`, { sample_text: sampleText });
  }
}