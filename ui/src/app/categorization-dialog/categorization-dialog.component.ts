import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-categorization-dialog',
  templateUrl: './categorization-dialog.component.html',
  styleUrls: ['./categorization-dialog.component.scss'],
  standalone: true,
  imports: [CommonModule, FormsModule]
})
export class CategorizationDialogComponent {
  categories: string[] = ['Invoice', 'Finance'];

  addCategory(category: string) {
    if (category && !this.categories.includes(category)) {
      this.categories.push(category);
    }
  }

  removeCategory(category: string) {
    this.categories = this.categories.filter(c => c !== category);
  }
}
