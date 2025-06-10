import axios from "axios";
import {
  fetchTemplates,
  fetchTemplate,
  createTemplate,
  updateTemplate,
  deleteTemplate,
  fetchTemplateReviews,
  createReview,
  fetchCategories,
  fetchPendingTemplates,
  approveTemplate,
  fetchMarketplaceStats,
  fetchMyTemplates,
  Template,
  TemplateCreate,
  TemplateUpdate,
  TemplateList,
  TemplateSearch,
  Review,
  ReviewCreate,
  Category,
  TemplateApproval,
  MarketplaceStats,
} from "./marketplace";

// Mock axios
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe("marketplace API", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Template operations", () => {
    const mockTemplate: Template = {
      id: 1,
      name: "Test Template",
      description: "A test template",
      author_id: 1,
      category_id: 1,
      version: "1.0.0",
      docker_compose_yaml: "version: '3.8'\nservices:\n  app:\n    image: nginx",
      tags: ["test", "nginx"],
      status: "approved",
      downloads: 10,
      rating_avg: 4.5,
      rating_count: 2,
      created_at: "2023-01-01T00:00:00Z",
      updated_at: "2023-01-01T00:00:00Z",
      author_username: "testuser",
      category_name: "Web Servers",
    };

    const mockTemplateList: TemplateList = {
      templates: [mockTemplate],
      total: 1,
      page: 1,
      per_page: 20,
      pages: 1,
    };

    test("fetchTemplates should return template list", async () => {
      mockedAxios.get.mockResolvedValue({ data: mockTemplateList });

      const params: TemplateSearch = {
        query: "test",
        category_id: 1,
        page: 1,
        per_page: 20,
      };

      const result = await fetchTemplates(params);

      expect(mockedAxios.get).toHaveBeenCalledWith("/api/marketplace/templates", {
        params,
      });
      expect(result).toEqual(mockTemplateList);
    });

    test("fetchTemplate should return single template", async () => {
      mockedAxios.get.mockResolvedValue({ data: mockTemplate });

      const result = await fetchTemplate(1);

      expect(mockedAxios.get).toHaveBeenCalledWith("/api/marketplace/templates/1");
      expect(result).toEqual(mockTemplate);
    });

    test("createTemplate should create new template", async () => {
      const templateData: TemplateCreate = {
        name: "New Template",
        description: "A new template",
        category_id: 1,
        docker_compose_yaml: "version: '3.8'\nservices:\n  app:\n    image: nginx",
        tags: ["new", "test"],
        version: "1.0.0",
      };

      mockedAxios.post.mockResolvedValue({ data: mockTemplate });

      const result = await createTemplate(templateData);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        "/api/marketplace/templates",
        templateData
      );
      expect(result).toEqual(mockTemplate);
    });

    test("updateTemplate should update existing template", async () => {
      const updateData: TemplateUpdate = {
        name: "Updated Template",
        description: "Updated description",
      };

      mockedAxios.put.mockResolvedValue({ data: mockTemplate });

      const result = await updateTemplate(1, updateData);

      expect(mockedAxios.put).toHaveBeenCalledWith(
        "/api/marketplace/templates/1",
        updateData
      );
      expect(result).toEqual(mockTemplate);
    });

    test("deleteTemplate should delete template", async () => {
      mockedAxios.delete.mockResolvedValue({});

      await deleteTemplate(1);

      expect(mockedAxios.delete).toHaveBeenCalledWith("/api/marketplace/templates/1");
    });
  });

  describe("Review operations", () => {
    const mockReview: Review = {
      id: 1,
      template_id: 1,
      user_id: 1,
      rating: 5,
      comment: "Great template!",
      created_at: "2023-01-01T00:00:00Z",
      updated_at: "2023-01-01T00:00:00Z",
      username: "testuser",
    };

    test("fetchTemplateReviews should return reviews", async () => {
      mockedAxios.get.mockResolvedValue({ data: [mockReview] });

      const result = await fetchTemplateReviews(1);

      expect(mockedAxios.get).toHaveBeenCalledWith(
        "/api/marketplace/templates/1/reviews"
      );
      expect(result).toEqual([mockReview]);
    });

    test("createReview should create new review", async () => {
      const reviewData: ReviewCreate = {
        rating: 5,
        comment: "Excellent template!",
      };

      mockedAxios.post.mockResolvedValue({ data: mockReview });

      const result = await createReview(1, reviewData);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        "/api/marketplace/templates/1/reviews",
        reviewData
      );
      expect(result).toEqual(mockReview);
    });
  });

  describe("Category operations", () => {
    const mockCategory: Category = {
      id: 1,
      name: "Web Servers",
      description: "Web server templates",
      icon: "web",
      sort_order: 1,
      is_active: true,
      created_at: "2023-01-01T00:00:00Z",
      updated_at: "2023-01-01T00:00:00Z",
      template_count: 5,
    };

    test("fetchCategories should return categories", async () => {
      mockedAxios.get.mockResolvedValue({ data: [mockCategory] });

      const result = await fetchCategories();

      expect(mockedAxios.get).toHaveBeenCalledWith("/api/marketplace/categories");
      expect(result).toEqual([mockCategory]);
    });
  });

  describe("Admin operations", () => {
    const mockTemplate: Template = {
      id: 1,
      name: "Pending Template",
      description: "A pending template",
      author_id: 1,
      category_id: 1,
      version: "1.0.0",
      docker_compose_yaml: "version: '3.8'\nservices:\n  app:\n    image: nginx",
      tags: ["pending"],
      status: "pending",
      downloads: 0,
      rating_avg: 0,
      rating_count: 0,
      created_at: "2023-01-01T00:00:00Z",
      updated_at: "2023-01-01T00:00:00Z",
    };

    const mockStats: MarketplaceStats = {
      total_templates: 10,
      approved_templates: 8,
      pending_templates: 1,
      rejected_templates: 1,
      total_reviews: 15,
      average_rating: 4.2,
      total_downloads: 100,
      top_categories: [
        { category_name: "Web Servers", template_count: 5 },
        { category_name: "Databases", template_count: 3 },
      ],
      recent_activity: [
        {
          action: "approved",
          template_name: "NGINX Template",
          timestamp: "2023-01-01T00:00:00Z",
        },
      ],
    };

    test("fetchPendingTemplates should return pending templates", async () => {
      mockedAxios.get.mockResolvedValue({ data: [mockTemplate] });

      const result = await fetchPendingTemplates();

      expect(mockedAxios.get).toHaveBeenCalledWith("/api/marketplace/admin/pending");
      expect(result).toEqual([mockTemplate]);
    });

    test("approveTemplate should approve template", async () => {
      const approvalData: TemplateApproval = {
        approved: true,
      };

      mockedAxios.post.mockResolvedValue({ data: mockTemplate });

      const result = await approveTemplate(1, approvalData);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        "/api/marketplace/admin/templates/1/approve",
        approvalData
      );
      expect(result).toEqual(mockTemplate);
    });

    test("fetchMarketplaceStats should return stats", async () => {
      mockedAxios.get.mockResolvedValue({ data: mockStats });

      const result = await fetchMarketplaceStats();

      expect(mockedAxios.get).toHaveBeenCalledWith("/api/marketplace/admin/stats");
      expect(result).toEqual(mockStats);
    });
  });

  describe("User templates", () => {
    const mockTemplate: Template = {
      id: 1,
      name: "My Template",
      description: "My template description",
      author_id: 1,
      category_id: 1,
      version: "1.0.0",
      docker_compose_yaml: "version: '3.8'\nservices:\n  app:\n    image: nginx",
      tags: ["mine"],
      status: "approved",
      downloads: 5,
      rating_avg: 4.0,
      rating_count: 1,
      created_at: "2023-01-01T00:00:00Z",
      updated_at: "2023-01-01T00:00:00Z",
    };

    test("fetchMyTemplates should return user templates", async () => {
      mockedAxios.get.mockResolvedValue({ data: [mockTemplate] });

      const result = await fetchMyTemplates();

      expect(mockedAxios.get).toHaveBeenCalledWith("/api/marketplace/my-templates");
      expect(result).toEqual([mockTemplate]);
    });
  });
});
