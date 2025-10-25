
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTableModule } from '@angular/material/table';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-category-management',
  standalone: true,
  imports: [CommonModule, MatTableModule, MatIconModule],
  templateUrl: './category-management.component.html',
  styleUrls: ['./category-management.component.scss']
})
export class CategoryManagementComponent implements OnInit {
  displayedColumns: string[] = ['name', 'description', 'actions'];
  dataSource = [
    {name: 'Invoices', description: 'Invoices from vendors'},
    {name: 'Contracts', description: 'Signed contracts with clients'},
  ];

  constructor() { }

  ngOnInit(): void {
  }

}
