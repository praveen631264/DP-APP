/*
MongoDB Setup and Examples

This script contains the commands for setting up the IntelliDocs collections and indexes in MongoDB. This is the NoSQL equivalent of DDL and DML.

Execute these commands using the MongoDB Shell (`mongosh`) against a database with Atlas Search enabled.
*/

// --- Data Definition Language (DDL) Equivalents ---

// Switch to your database (e.g., 'intellidocs')
use('intellidocs');

// 1. Create the 'documents' collection with validation (recommended)
db.createCollection('documents', {
  validator: { 
    $jsonSchema: {
      bsonType: "object",
      required: [ "filename", "content_type", "file_id", "status", "created_at" ],
      properties: {
        filename: { bsonType: "string" },
        content_type: { bsonType: "string" },
        file_id: { bsonType: "objectId" },
        status: { bsonType: "string" },
        created_at: { bsonType: "date" },
        processed_at: { bsonType: ["date", "null"] },
        kvps: { bsonType: "object" },
        category: { bsonType: ["string", "null"] },
        text: { bsonType: ["string", "null"] },
        embedding: { bsonType: ["array", "null"] }
      }
    }
  }
});

// 2. The 'fs.files' and 'fs.chunks' collections for GridFS are created automatically.


// --- Index Creation ---

// 1. Create an index on the 'category' field for faster filtering.
print("Creating index on 'category'...");
db.documents.createIndex({ "category": 1 });

// 2. Create an index on the 'status' field for faster status-based queries.
print("Creating index on 'status'...");
db.documents.createIndex({ "status": 1 });

// 3. Create a Vector Search Index for AI-powered semantic search (Requires Atlas Search)
// This definition matches the one in the application code.
const vectorIndexName = "vector_index";
print(`Creating Atlas Vector Search index '${vectorIndexName}'. This may take a minute...`);
db.documents.createSearchIndex({
    "name": vectorIndexName,
    "definition": {
        "mappings": {
            "dynamic": true,
            "fields": {
                "embedding": {
                    "type": "vector",
                    "dimensions": 1536, // Match the dimensions of your embedding model
                    "similarity": "cosine"
                }
            }
        }
    }
});

print("All collections and indexes have been set up.");


// --- Data Manipulation Language (DML) Equivalents ---

// Example 1: Inserting a new document (typically done by the application)
db.documents.insertOne({
    "filename": "test_invoice.pdf",
    "content_type": "application/pdf",
    "file_id": new ObjectId(),
    "status": "Queued for Processing",
    "created_at": new Date(),
    "processed_at": null,
    "kvps": {},
    "category": null,
    "embedding": null
});

// Example 2: Finding all documents in the 'Invoices' category (uses the 'category' index)
db.documents.find({
    "category": "Invoices"
});

// Example 3: Updating a document after processing
db.documents.updateOne(
    { "_id": new ObjectId("YOUR_DOCUMENT_ID_HERE") },
    { 
        $set: {
            "status": "Processed",
            "processed_at": new Date(),
            "category": "Invoice",
            "text": "This is the extracted text...",
            "kvps": { "Invoice Number": "INV-123", "Total": "$500" },
            "embedding": [ 0.12, 0.54, ... ] // Array of embedding floats
        }
    }
);
