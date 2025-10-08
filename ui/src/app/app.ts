import { Component, OnInit, ElementRef, ViewChild, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpEventType } from '@angular/common/http';
import { CategoryService, Category } from './category.service';
import { DocumentService, Document } from './document.service';

declare var lucide: any;

@Component({
  selector: 'app-root',
  templateUrl: './app.html',
  styleUrls: ['./app.scss'],
  standalone: true,
  imports: [CommonModule, FormsModule]
})
export class App implements OnInit, AfterViewInit {
  selectedDocument: Document | null = null;
  isKVRefinementChatOpen = false;
  isCategoryModalOpen = false;
  isSidebarOpen = false;

  constructor(
    private documentService: DocumentService,
    private categoryService: CategoryService
  ) {}

  ngOnInit(): void {
    // Logic to run on component initialization
  }

  ngAfterViewInit(): void {
    lucide.createIcons();
  }

  toggleSidebar(): void {
    this.isSidebarOpen = !this.isSidebarOpen;
  }

  deleteKVRow(key: string): void {
    if (this.selectedDocument && this.selectedDocument.kvData) {
      this.selectedDocument.kvData = this.selectedDocument.kvData.filter(item => item.key !== key);
    }
  }
}
