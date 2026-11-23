export interface paths {
    "/api/_atlas/agents": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Agents
         * @description List the app's agents without exposing credentials or upstream URLs.
         */
        get: operations["list_agents_api__atlas_agents_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/_atlas/agents/paired": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Paired Agent
         * @description Return the agent built in this app's Build chat.
         */
        get: operations["get_paired_agent_api__atlas_agents_paired_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/_atlas/agents/{agent_identifier}/threads": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Threads */
        get: operations["list_threads_api__atlas_agents__agent_identifier__threads_get"];
        put?: never;
        /** Create Thread */
        post: operations["create_thread_api__atlas_agents__agent_identifier__threads_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/_atlas/agents/{agent_identifier}/threads/{thread_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Thread */
        get: operations["get_thread_api__atlas_agents__agent_identifier__threads__thread_id__get"];
        put?: never;
        post?: never;
        /** Delete Thread */
        delete: operations["delete_thread_api__atlas_agents__agent_identifier__threads__thread_id__delete"];
        options?: never;
        head?: never;
        /** Rename Thread */
        patch: operations["rename_thread_api__atlas_agents__agent_identifier__threads__thread_id__patch"];
        trace?: never;
    };
    "/api/_atlas/agents/{agent_identifier}/threads/{thread_id}/pin": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Pin Thread */
        post: operations["pin_thread_api__atlas_agents__agent_identifier__threads__thread_id__pin_post"];
        /** Unpin Thread */
        delete: operations["unpin_thread_api__atlas_agents__agent_identifier__threads__thread_id__pin_delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/_atlas/agents/{agent_identifier}/threads/{thread_id}/uploads": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Upload File */
        post: operations["upload_file_api__atlas_agents__agent_identifier__threads__thread_id__uploads_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/_atlas/agents/{agent_identifier}/threads/{thread_id}/files": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Thread Files */
        get: operations["list_thread_files_api__atlas_agents__agent_identifier__threads__thread_id__files_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/_atlas/agents/{agent_identifier}/threads/{thread_id}/files/{file_id}/content": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Download Thread File */
        get: operations["download_thread_file_api__atlas_agents__agent_identifier__threads__thread_id__files__file_id__content_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/_atlas/agents/{agent_identifier}/chat": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Send Message */
        post: operations["send_message_api__atlas_agents__agent_identifier__chat_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/_atlas/agents/{agent_identifier}/chat/stream": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Stream Message */
        post: operations["stream_message_api__atlas_agents__agent_identifier__chat_stream_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/_atlas/agents/{agent_identifier}/chat/resume": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Resume Message */
        post: operations["resume_message_api__atlas_agents__agent_identifier__chat_resume_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/_atlas/agents/{agent_identifier}/chat/attach": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Attach Message */
        post: operations["attach_message_api__atlas_agents__agent_identifier__chat_attach_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/_atlas/agents/{agent_identifier}/chat/stop": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Stop Message */
        post: operations["stop_message_api__atlas_agents__agent_identifier__chat_stop_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/_atlas/agents/{agent_identifier}/calls/{call_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Get Call */
        post: operations["get_call_api__atlas_agents__agent_identifier__calls__call_id__post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/_atlas/agents/{agent_identifier}/calls/{call_id}/events": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Subscribe Call */
        post: operations["subscribe_call_api__atlas_agents__agent_identifier__calls__call_id__events_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/_atlas/agents/{agent_identifier}/calls/{call_id}/recording": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Call Recording */
        post: operations["call_recording_api__atlas_agents__agent_identifier__calls__call_id__recording_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/_atlas/agents/{agent_identifier}/calls/{call_id}/delete": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Delete Call */
        post: operations["delete_call_api__atlas_agents__agent_identifier__calls__call_id__delete_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Health */
        get: operations["health_api_health_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/notes/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Notes */
        get: operations["list_notes_api_notes__get"];
        put?: never;
        /** Create Note */
        post: operations["create_note_api_notes__post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/notes/{note_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Note */
        get: operations["get_note_api_notes__note_id__get"];
        /** Update Note */
        put: operations["update_note_api_notes__note_id__put"];
        post?: never;
        /** Delete Note */
        delete: operations["delete_note_api_notes__note_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/users/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Me */
        get: operations["get_me_api_users_me_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/users/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Users */
        get: operations["list_users_api_users__get"];
        put?: never;
        /** Create User */
        post: operations["create_user_api_users__post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/users/{user_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Update User */
        put: operations["update_user_api_users__user_id__put"];
        post?: never;
        /** Delete User */
        delete: operations["delete_user_api_users__user_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/catalog/overview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Overview */
        get: operations["get_overview_api_catalog_overview_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/catalog/sync-status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Sync Status */
        get: operations["get_sync_status_api_catalog_sync_status_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/catalog/products/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Products */
        get: operations["list_products_api_catalog_products__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/catalog/products/{product_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Product */
        get: operations["get_product_api_catalog_products__product_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/catalog/attributes": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Attribute Library */
        get: operations["get_attribute_library_api_catalog_attributes_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/catalog/lookup/products/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Lookup Products
         * @description Find products in the synced catalog by name, product code, description, or exact ID.
         */
        get: operations["lookup_products_api_catalog_lookup_products__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/catalog/products/{product_id}/description": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Live Description
         * @description Read the current description and LastModifiedDate live from Salesforce.
         */
        get: operations["get_live_description_api_catalog_products__product_id__description_get"];
        /**
         * Update Description
         * @description Write one confirmed description to Salesforce Product2.Description.
         *
         *     Requires confirm=true and the LastModifiedDate returned by the live read or
         *     preview; answers 409 without writing if the record changed since then.
         */
        put: operations["update_description_api_catalog_products__product_id__description_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/catalog/products/{product_id}/description/preview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Preview Description
         * @description Compare a proposed description with the live Salesforce value. Never writes.
         */
        post: operations["preview_description_api_catalog_products__product_id__description_preview_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/catalog/products/{product_id}/description/history": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Description History */
        get: operations["description_history_api_catalog_products__product_id__description_history_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/sync/catalog/start-full": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Start Full
         * @description Start a full refresh: re-read everything and drop records deleted in Salesforce.
         */
        post: operations["start_full_api_sync_catalog_start_full_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/sync/catalog/start": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Start */
        post: operations["start_api_sync_catalog_start_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/sync/catalog/{job_id}/tick": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Tick */
        post: operations["tick_api_sync_catalog__job_id__tick_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** AttributeCategoryItem */
        AttributeCategoryItem: {
            /** Sf Id */
            sf_id: string;
            /** Name */
            name: string | null;
            /** Code */
            code: string | null;
            /** Description */
            description: string | null;
            /** Attributes */
            attributes: components["schemas"]["RecordRef"][];
        };
        /** AttributeDefinitionItem */
        AttributeDefinitionItem: {
            /** Sf Id */
            sf_id: string;
            /** Name */
            name: string | null;
            /** Label */
            label: string | null;
            /** Code */
            code: string | null;
            /** Developer Name */
            developer_name: string | null;
            /** Description */
            description: string | null;
            /** Data Type */
            data_type: string | null;
            /** Is Active */
            is_active: boolean | null;
            /** Is Required */
            is_required: boolean | null;
            /** Default Value */
            default_value: string | null;
            picklist: components["schemas"]["RecordRef"] | null;
            /** Picklist Values */
            picklist_values: components["schemas"]["PicklistValueItem"][];
            /** Categories */
            categories: components["schemas"]["RecordRef"][];
            /** Classification Count */
            classification_count: number;
            /** Product Count */
            product_count: number;
        };
        /** AttributeLibrary */
        AttributeLibrary: {
            /** Definitions */
            definitions: components["schemas"]["AttributeDefinitionItem"][];
            /** Categories */
            categories: components["schemas"]["AttributeCategoryItem"][];
            /** Picklists */
            picklists: components["schemas"]["PicklistItem"][];
            /** Classifications */
            classifications: components["schemas"]["ClassificationItem"][];
            /** Sections */
            sections: components["schemas"]["SectionAvailability"][];
        };
        /** BundleComponentItem */
        BundleComponentItem: {
            /** Sf Id */
            sf_id: string;
            child_product: components["schemas"]["RecordRef"] | null;
            child_classification: components["schemas"]["RecordRef"] | null;
            /** Relationship Type */
            relationship_type: string | null;
            /** Quantity */
            quantity: number | null;
            /** Min Quantity */
            min_quantity: number | null;
            /** Max Quantity */
            max_quantity: number | null;
            /** Is Required */
            is_required: boolean | null;
            /** Is Default */
            is_default: boolean | null;
            /** Is Quantity Editable */
            is_quantity_editable: boolean | null;
            /** Price Included In Bundle */
            price_included_in_bundle: boolean | null;
            /** Sequence */
            sequence: number | null;
        };
        /** BundleGroupItem */
        BundleGroupItem: {
            /** Sf Id */
            sf_id: string;
            /** Name */
            name: string | null;
            /** Code */
            code: string | null;
            /** Description */
            description: string | null;
            /** Parent Group Id */
            parent_group_id: string | null;
            /** Min Components */
            min_components: number | null;
            /** Max Components */
            max_components: number | null;
            /** Sequence */
            sequence: number | null;
            /** Components */
            components: components["schemas"]["BundleComponentItem"][];
        };
        /** BundleStructure */
        BundleStructure: {
            /** Groups */
            groups: components["schemas"]["BundleGroupItem"][];
            /** Ungrouped Components */
            ungrouped_components: components["schemas"]["BundleComponentItem"][];
        };
        /** CatalogOverview */
        CatalogOverview: {
            sync: components["schemas"]["CatalogSyncStatus"];
            totals: components["schemas"]["CatalogTotals"];
            /** Catalogs */
            catalogs: components["schemas"]["CatalogSummary"][];
            /** Sections */
            sections: components["schemas"]["SectionAvailability"][];
            /** Coverage */
            coverage: components["schemas"]["CoverageItem"][];
            /** Salesforce Instance Url */
            salesforce_instance_url: string | null;
        };
        /** CatalogSummary */
        CatalogSummary: {
            /** Sf Id */
            sf_id: string;
            /** Name */
            name: string | null;
            /** Code */
            code: string | null;
            /** Description */
            description: string | null;
            /** Catalog Type */
            catalog_type: string | null;
            /** Effective Start */
            effective_start: string | null;
            /** Effective End */
            effective_end: string | null;
            /** Category Count */
            category_count: number;
            /** Product Count */
            product_count: number;
            /** Categories */
            categories: components["schemas"]["CategoryNode"][];
        };
        /** CatalogSyncStatus */
        CatalogSyncStatus: {
            /** Has Synced */
            has_synced: boolean;
            /** Last Synced At */
            last_synced_at: string | null;
            /** Last Job Status */
            last_job_status: string | null;
            /** Last Job Mode */
            last_job_mode: string | null;
            /** Last Job Finished At */
            last_job_finished_at: string | null;
            /** Last Failure Reason */
            last_failure_reason: string | null;
        };
        /** CatalogTotals */
        CatalogTotals: {
            /** Catalogs */
            catalogs: number;
            /** Categories */
            categories: number;
            /** Products */
            products: number;
            /** Classifications */
            classifications: number;
            /** Attribute Definitions */
            attribute_definitions: number;
            /** Price Books */
            price_books: number;
            /** Bundles */
            bundles: number;
        };
        /** CategoryMembership */
        CategoryMembership: {
            /** Sf Id */
            sf_id: string;
            catalog: components["schemas"]["RecordRef"] | null;
            category: components["schemas"]["RecordRef"] | null;
            /** Category Path */
            category_path: string[];
        };
        /** CategoryNode */
        CategoryNode: {
            /** Sf Id */
            sf_id: string;
            /** Name */
            name: string | null;
            /** Code */
            code: string | null;
            /** Description */
            description: string | null;
            /** Sort Order */
            sort_order: number | null;
            /** Is Navigational */
            is_navigational: boolean | null;
            /** Product Count */
            product_count: number;
            /** Total Product Count */
            total_product_count: number;
            /** Children */
            children: components["schemas"]["CategoryNode"][];
        };
        /** ClassificationAttributeItem */
        ClassificationAttributeItem: {
            /** Sf Id */
            sf_id: string;
            /** Name */
            name: string | null;
            definition: components["schemas"]["RecordRef"] | null;
            category: components["schemas"]["RecordRef"] | null;
            /** Is Required */
            is_required: boolean | null;
            /** Default Value */
            default_value: string | null;
            /** Status */
            status: string | null;
        };
        /** ClassificationItem */
        ClassificationItem: {
            /** Sf Id */
            sf_id: string;
            /** Name */
            name: string | null;
            /** Code */
            code: string | null;
            /** Status */
            status: string | null;
            parent: components["schemas"]["RecordRef"] | null;
            /** Product Count */
            product_count: number;
            /** Attributes */
            attributes: components["schemas"]["ClassificationAttributeItem"][];
        };
        /** CoverageItem */
        CoverageItem: {
            /** Object Api Name */
            object_api_name: string;
            /** Label */
            label: string;
            /** Section */
            section: string;
            /** Mapped */
            mapped: boolean;
            /**
             * Status
             * @enum {string}
             */
            status: "synced" | "empty" | "not_mapped" | "not_available" | "blocked" | "error" | "never_synced";
            /** Salesforce Count */
            salesforce_count: number | null;
            /** Cached Count */
            cached_count: number;
            /** Missing Fields */
            missing_fields: string[];
            /** Detail */
            detail: string | null;
            /** Checked At */
            checked_at: string | null;
        };
        /** DescriptionChangeItem */
        DescriptionChangeItem: {
            /** Id */
            id: number;
            /** Product Sf Id */
            product_sf_id: string;
            /** Product Name */
            product_name: string | null;
            /** Outcome */
            outcome: string;
            /** Previous Description */
            previous_description: string | null;
            /** Proposed Description */
            proposed_description: string;
            /** Error Detail */
            error_detail: string | null;
            /** Requested By */
            requested_by: string;
            /**
             * Expected Last Modified
             * Format: date-time
             */
            expected_last_modified: string;
            /** Salesforce Last Modified After */
            salesforce_last_modified_after: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** DescriptionPreview */
        DescriptionPreview: {
            /** Product Sf Id */
            product_sf_id: string;
            /** Product Name */
            product_name: string | null;
            /** Current Description */
            current_description: string | null;
            /** Proposed Description */
            proposed_description: string;
            /** Changed */
            changed: boolean;
            /** Clears Description */
            clears_description: boolean;
            /** Proposed Length */
            proposed_length: number;
            /** Max Length */
            max_length: number;
            /** Writable */
            writable: boolean;
            /**
             * Last Modified
             * Format: date-time
             */
            last_modified: string;
            /** Problems */
            problems: string[];
            /** Can Apply */
            can_apply: boolean;
        };
        /** DescriptionPreviewRequest */
        DescriptionPreviewRequest: {
            /** Proposed Description */
            proposed_description: string;
        };
        /** DescriptionUpdateRequest */
        DescriptionUpdateRequest: {
            /** Proposed Description */
            proposed_description: string;
            /**
             * Expected Last Modified
             * Format: date-time
             */
            expected_last_modified: string;
            /** Confirm */
            confirm: boolean;
        };
        /** DescriptionUpdateResult */
        DescriptionUpdateResult: {
            /** Change Id */
            change_id: number;
            /** Product Sf Id */
            product_sf_id: string;
            /** Product Name */
            product_name: string | null;
            /** Previous Description */
            previous_description: string | null;
            /** Description */
            description: string | null;
            /**
             * Last Modified
             * Format: date-time
             */
            last_modified: string;
            /** Verified */
            verified: boolean;
        };
        /** FieldMetadataOut */
        FieldMetadataOut: {
            /** Object Api Name */
            object_api_name: string;
            /** Field Api Name */
            field_api_name: string;
            /** Label */
            label: string;
            /** Type */
            type: string;
            /** Max Length */
            max_length: number;
            /** Updateable */
            updateable: boolean;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** HealthResponse */
        HealthResponse: {
            /** Status */
            status: string;
        };
        /** LiveDescription */
        LiveDescription: {
            /** Product Sf Id */
            product_sf_id: string;
            /** Product Name */
            product_name: string | null;
            /** Current Description */
            current_description: string | null;
            /**
             * Last Modified
             * Format: date-time
             */
            last_modified: string;
            /** Last Modified By */
            last_modified_by: string | null;
            field: components["schemas"]["FieldMetadataOut"];
            /** Cached Description */
            cached_description: string | null;
            /** Cache Was Stale */
            cache_was_stale: boolean;
        };
        /** MeResponse */
        MeResponse: {
            /** Email */
            email: string;
            /** Name */
            name: string;
            /** Role */
            role: string;
            /** Is Admin */
            is_admin: boolean;
        };
        /** NoteCreate */
        NoteCreate: {
            /** Title */
            title: string;
            /** Body */
            body: string;
        };
        /** NoteResponse */
        NoteResponse: {
            /** Id */
            id: number;
            /** Title */
            title: string;
            /** Body */
            body: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** NoteUpdate */
        NoteUpdate: {
            /** Title */
            title: string;
            /** Body */
            body: string;
        };
        /** PicklistItem */
        PicklistItem: {
            /** Sf Id */
            sf_id: string;
            /** Name */
            name: string | null;
            /** Code */
            code: string | null;
            /** Status */
            status: string | null;
            /** Data Type */
            data_type: string | null;
            /** Values */
            values: components["schemas"]["PicklistValueItem"][];
        };
        /** PicklistValueItem */
        PicklistValueItem: {
            /** Sf Id */
            sf_id: string;
            /** Label */
            label: string | null;
            /** Value */
            value: string | null;
            /** Code */
            code: string | null;
            /** Is Default */
            is_default: boolean | null;
            /** Sequence */
            sequence: number | null;
            /** Status */
            status: string | null;
        };
        /** PriceEntryItem */
        PriceEntryItem: {
            /** Sf Id */
            sf_id: string;
            price_book: components["schemas"]["RecordRef"] | null;
            /** Price Book Is Standard */
            price_book_is_standard: boolean | null;
            /** Unit Price */
            unit_price: number | null;
            /** Is Active */
            is_active: boolean | null;
            /** Use Standard Price */
            use_standard_price: boolean | null;
            selling_model: components["schemas"]["RecordRef"] | null;
        };
        /** ProductAttributeItem */
        ProductAttributeItem: {
            /** Sf Id */
            sf_id: string;
            /**
             * Source
             * @enum {string}
             */
            source: "product" | "classification";
            /** Name */
            name: string | null;
            definition: components["schemas"]["RecordRef"] | null;
            /** Data Type */
            data_type: string | null;
            category: components["schemas"]["RecordRef"] | null;
            /** Default Value */
            default_value: string | null;
            /** Is Required */
            is_required: boolean | null;
            /** Is Hidden */
            is_hidden: boolean | null;
            /** Is Read Only */
            is_read_only: boolean | null;
            /** Is Price Impacting */
            is_price_impacting: boolean | null;
            /** Status */
            status: string | null;
            /** Sequence */
            sequence: number | null;
            /** Display Type */
            display_type: string | null;
            /** Picklist Values */
            picklist_values: components["schemas"]["PicklistValueItem"][];
            /** Excluded Picklist Values */
            excluded_picklist_values: string | null;
        };
        /** ProductDetail */
        ProductDetail: {
            /** Sf Id */
            sf_id: string;
            /** Name */
            name: string | null;
            /** Product Code */
            product_code: string | null;
            /** Description */
            description: string | null;
            /** Is Active */
            is_active: boolean | null;
            /** Is Archived */
            is_archived: boolean | null;
            /** Family */
            family: string | null;
            /** Type */
            type: string | null;
            /** Configure During Sale */
            configure_during_sale: string | null;
            /** Stock Keeping Unit */
            stock_keeping_unit: string | null;
            /** Quantity Unit Of Measure */
            quantity_unit_of_measure: string | null;
            /** Specification Type */
            specification_type: string | null;
            /** Decomposition Scope */
            decomposition_scope: string | null;
            /** Usage Model Type */
            usage_model_type: string | null;
            /** Is Assetizable */
            is_assetizable: boolean | null;
            /** Is Sold Only With Other Products */
            is_sold_only_with_other_products: boolean | null;
            /** Availability Date */
            availability_date: string | null;
            /** Discontinued Date */
            discontinued_date: string | null;
            /** End Of Life Date */
            end_of_life_date: string | null;
            /** Help Text */
            help_text: string | null;
            /** Display Url */
            display_url: string | null;
            /** Last Modified */
            last_modified: string | null;
            /**
             * Synced At
             * Format: date-time
             */
            synced_at: string;
            /** Salesforce Url */
            salesforce_url: string | null;
            classification: components["schemas"]["RecordRef"] | null;
            /** Memberships */
            memberships: components["schemas"]["CategoryMembership"][];
            /** Attributes */
            attributes: components["schemas"]["ProductAttributeItem"][];
            bundle: components["schemas"]["BundleStructure"] | null;
            /** Used In Bundles */
            used_in_bundles: components["schemas"]["RecordRef"][];
            /** Selling Models */
            selling_models: components["schemas"]["SellingModelItem"][];
            /** Price Entries */
            price_entries: components["schemas"]["PriceEntryItem"][];
            /** Sections */
            sections: components["schemas"]["SectionAvailability"][];
        };
        /** ProductListItem */
        ProductListItem: {
            /** Sf Id */
            sf_id: string;
            /** Name */
            name: string | null;
            /** Product Code */
            product_code: string | null;
            /** Type */
            type: string | null;
            /** Family */
            family: string | null;
            /** Is Active */
            is_active: boolean | null;
            /** Description */
            description: string | null;
            classification: components["schemas"]["RecordRef"] | null;
            /** Category Names */
            category_names: string[];
            /** Last Modified */
            last_modified: string | null;
        };
        /** ProductLookupItem */
        ProductLookupItem: {
            /** Sf Id */
            sf_id: string;
            /** Name */
            name: string | null;
            /** Product Code */
            product_code: string | null;
            /** Type */
            type: string | null;
            /** Is Active */
            is_active: boolean | null;
            /** Description */
            description: string | null;
            /** Catalog Names */
            catalog_names: string[];
            /** Category Names */
            category_names: string[];
        };
        /** ProductLookupResponse */
        ProductLookupResponse: {
            /** Query */
            query: string;
            /** Items */
            items: components["schemas"]["ProductLookupItem"][];
            /** Total Matches */
            total_matches: number;
            /** Last Synced At */
            last_synced_at: string | null;
        };
        /** ProductPage */
        ProductPage: {
            /** Items */
            items: components["schemas"]["ProductListItem"][];
            /** Total */
            total: number;
            /** Page */
            page: number;
            /** Page Size */
            page_size: number;
            /** Total Pages */
            total_pages: number;
        };
        /** PublicAgentResponse */
        PublicAgentResponse: {
            /** Id */
            id: string;
            /** Slug */
            slug: string;
            /** Name */
            name: string;
            /** Description */
            description: string;
        };
        /** RecordRef */
        RecordRef: {
            /** Sf Id */
            sf_id: string;
            /** Name */
            name?: string | null;
            /** Code */
            code?: string | null;
        };
        /** SectionAvailability */
        SectionAvailability: {
            /** Section */
            section: string;
            /** Available */
            available: boolean;
            /**
             * Status
             * @enum {string}
             */
            status: "synced" | "empty" | "not_mapped" | "not_available" | "blocked" | "error" | "never_synced";
            /** Blocked Objects */
            blocked_objects: string[];
            /** Detail */
            detail: string | null;
        };
        /** SellingModelItem */
        SellingModelItem: {
            /** Sf Id */
            sf_id: string;
            selling_model: components["schemas"]["RecordRef"] | null;
            /** Selling Model Type */
            selling_model_type: string | null;
            /** Pricing Term */
            pricing_term: number | null;
            /** Pricing Term Unit */
            pricing_term_unit: string | null;
            /** Status */
            status: string | null;
            /** Is Default */
            is_default: boolean | null;
        };
        /** SyncJobView */
        SyncJobView: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Status
             * @enum {string}
             */
            status: "pending" | "running" | "success" | "failed";
            /** Records Synced */
            records_synced: number;
            /** Finished */
            finished: boolean;
            /** Failure Reason */
            failure_reason?: string | null;
            /** Finished At */
            finished_at?: string | null;
        };
        /** UserCreate */
        UserCreate: {
            /** Email */
            email: string;
            /**
             * Name
             * @default
             */
            name: string;
            /**
             * Role
             * @default viewer
             * @enum {string}
             */
            role: "admin" | "viewer";
        };
        /** UserResponse */
        UserResponse: {
            /** Id */
            id: number;
            /** Email */
            email: string;
            /** Name */
            name: string;
            /** Role */
            role: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** UserUpdate */
        UserUpdate: {
            /** Name */
            name?: string | null;
            /**
             * Role
             * @enum {string}
             */
            role: "admin" | "viewer";
        };
        /** ValidationError */
        ValidationError: {
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
            /** Input */
            input?: unknown;
            /** Context */
            ctx?: Record<string, never>;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    list_agents_api__atlas_agents_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PublicAgentResponse"][];
                };
            };
        };
    };
    get_paired_agent_api__atlas_agents_paired_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PublicAgentResponse"];
                };
            };
        };
    };
    list_threads_api__atlas_agents__agent_identifier__threads_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                agent_identifier: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_thread_api__atlas_agents__agent_identifier__threads_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                agent_identifier: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_thread_api__atlas_agents__agent_identifier__threads__thread_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                agent_identifier: string;
                thread_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_thread_api__atlas_agents__agent_identifier__threads__thread_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                agent_identifier: string;
                thread_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    rename_thread_api__atlas_agents__agent_identifier__threads__thread_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                agent_identifier: string;
                thread_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    pin_thread_api__atlas_agents__agent_identifier__threads__thread_id__pin_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                agent_identifier: string;
                thread_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    unpin_thread_api__atlas_agents__agent_identifier__threads__thread_id__pin_delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                agent_identifier: string;
                thread_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    upload_file_api__atlas_agents__agent_identifier__threads__thread_id__uploads_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                agent_identifier: string;
                thread_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_thread_files_api__atlas_agents__agent_identifier__threads__thread_id__files_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                agent_identifier: string;
                thread_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    download_thread_file_api__atlas_agents__agent_identifier__threads__thread_id__files__file_id__content_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                agent_identifier: string;
                thread_id: string;
                file_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    send_message_api__atlas_agents__agent_identifier__chat_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                agent_identifier: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    stream_message_api__atlas_agents__agent_identifier__chat_stream_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                agent_identifier: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    resume_message_api__atlas_agents__agent_identifier__chat_resume_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                agent_identifier: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    attach_message_api__atlas_agents__agent_identifier__chat_attach_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                agent_identifier: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    stop_message_api__atlas_agents__agent_identifier__chat_stop_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                agent_identifier: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_call_api__atlas_agents__agent_identifier__calls__call_id__post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                agent_identifier: string;
                call_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    subscribe_call_api__atlas_agents__agent_identifier__calls__call_id__events_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                agent_identifier: string;
                call_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    call_recording_api__atlas_agents__agent_identifier__calls__call_id__recording_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                agent_identifier: string;
                call_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_call_api__atlas_agents__agent_identifier__calls__call_id__delete_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                agent_identifier: string;
                call_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    health_api_health_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HealthResponse"];
                };
            };
        };
    };
    list_notes_api_notes__get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NoteResponse"][];
                };
            };
        };
    };
    create_note_api_notes__post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["NoteCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NoteResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_note_api_notes__note_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                note_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NoteResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_note_api_notes__note_id__put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                note_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["NoteUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NoteResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_note_api_notes__note_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                note_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_me_api_users_me_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MeResponse"];
                };
            };
        };
    };
    list_users_api_users__get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserResponse"][];
                };
            };
        };
    };
    create_user_api_users__post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UserCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_user_api_users__user_id__put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UserUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["UserResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_user_api_users__user_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_overview_api_catalog_overview_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CatalogOverview"];
                };
            };
        };
    };
    get_sync_status_api_catalog_sync_status_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CatalogSyncStatus"];
                };
            };
        };
    };
    list_products_api_catalog_products__get: {
        parameters: {
            query?: {
                q?: string | null;
                catalog_id?: string | null;
                category_id?: string | null;
                classification_id?: string | null;
                product_type?: ("bundle" | "simple") | null;
                is_active?: boolean | null;
                page?: number;
                page_size?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProductPage"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_product_api_catalog_products__product_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                /** @description Exact 18-character Salesforce Product2 record ID */
                product_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProductDetail"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_attribute_library_api_catalog_attributes_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AttributeLibrary"];
                };
            };
        };
    };
    lookup_products_api_catalog_lookup_products__get: {
        parameters: {
            query: {
                q: string;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProductLookupResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_live_description_api_catalog_products__product_id__description_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                /** @description Exact 18-character Salesforce Product2 record ID */
                product_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LiveDescription"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_description_api_catalog_products__product_id__description_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                /** @description Exact 18-character Salesforce Product2 record ID */
                product_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DescriptionUpdateRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DescriptionUpdateResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    preview_description_api_catalog_products__product_id__description_preview_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                /** @description Exact 18-character Salesforce Product2 record ID */
                product_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DescriptionPreviewRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DescriptionPreview"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    description_history_api_catalog_products__product_id__description_history_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                /** @description Exact 18-character Salesforce Product2 record ID */
                product_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DescriptionChangeItem"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    start_full_api_sync_catalog_start_full_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SyncJobView"];
                };
            };
        };
    };
    start_api_sync_catalog_start_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SyncJobView"];
                };
            };
        };
    };
    tick_api_sync_catalog__job_id__tick_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                job_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SyncJobView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
}
