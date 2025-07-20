import { useAppStore } from '../appStore';
import ProjectCanvas from './ProjectCanvas';
import ComponentCanvas from './ComponentCanvas';
import PropertiesPanel from './PropertiesPanel';
import { Resizer } from './Workspace';
import { DatasheetSplitView } from './DatasheetSplitView';
import { updateParsedData } from '../services/fileApi';

const MainPanel = () => {
  const { route, activeDatasheet, setActiveDatasheet, updateUpload } = useAppStore();

  const handleSave = async (id: string, payload: any) => {
    try {
      const updated = await updateParsedData(id, payload);
      setActiveDatasheet({ id: updated.id, url: updated.url, payload: updated.parsed_payload });
      updateUpload(id, {
        parsed_at: updated.parsed_at,
        is_human_verified: true,
      });
    } catch (error) {
      console.error('Failed to save datasheet', error);
    }
  };

  if (activeDatasheet) {
    return (
      <div className="[grid-area:workspace] h-full">
        <DatasheetSplitView
          assetId={activeDatasheet.id}
          pdfUrl={activeDatasheet.url}
          initialParsedData={activeDatasheet.payload}
          onClose={() => setActiveDatasheet(null)}
          onSave={handleSave}
        />
      </div>
    );
  }

  return (
    <main className="[grid-area:workspace] bg-gray-50 p-4 flex overflow-auto">
      <div className="flex-grow h-full relative">
        {(() => {
          switch (route) {
            case 'projects':
              return <ProjectCanvas />;
            case 'components':
              return <ComponentCanvas />;
          }
        })()}
      </div>
      <Resizer />
      <div className="w-[300px]">
        <PropertiesPanel />
      </div>
    </main>
  );
};

export default MainPanel;
