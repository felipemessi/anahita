import type { LocationTreeNode } from "@/types/world";

const LOCATION_TYPE_LABEL: Record<string, string> = {
  city: "Cidade",
  town: "Vila",
  dungeon: "Masmorra",
  wilderness: "Terras selvagens",
  building: "Edificação",
  region: "Região",
  plane: "Plano",
};

function LocationTreeItem({ node }: { node: LocationTreeNode }) {
  const label = (
    <span>
      {node.name}{" "}
      <span className="text-xs text-muted-foreground">
        ({LOCATION_TYPE_LABEL[node.location_type] ?? node.location_type})
      </span>
    </span>
  );

  if (node.children.length === 0) {
    return <li>{label}</li>;
  }

  return (
    <li>
      <details open>
        <summary className="cursor-pointer">{label}</summary>
        <ul className="ml-4 mt-1 space-y-1 border-l border-border pl-3">
          {node.children.map((child) => (
            <LocationTreeItem key={child.id} node={child} />
          ))}
        </ul>
      </details>
    </li>
  );
}

/** Expandable region → city → tavern tree (backend GET .../locations/tree). */
export function LocationTree({ tree }: { tree: LocationTreeNode[] }) {
  if (tree.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Nenhum local nesta campanha ainda.
      </p>
    );
  }
  return (
    <ul className="space-y-1 text-sm">
      {tree.map((node) => (
        <LocationTreeItem key={node.id} node={node} />
      ))}
    </ul>
  );
}
